from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Sum, Count
from decimal import Decimal

from .models import Cliente, Factura, DetalleFactura
from inventario.models import Producto, InventarioSucursal, MovimientoInventario
from sucursales.models import Sucursal
from usuarios.views import registrar_actividad


def obtener_sucursal_usuario(request):
    """
    Devuelve la sucursal seleccionada.
    - SUPER_ADMIN: puede trabajar sin sucursal (ve todo) o escoger una
    - Otros roles: DEBEN tener sucursal asignada o en sesión
    """
    # Si es SUPER_ADMIN, puede trabajar sin sucursal
    if request.user.rol == 'SUPER_ADMIN':
        sucursal_id = request.session.get('sucursal_actual')
        if sucursal_id:
            try:
                return Sucursal.objects.get(id=sucursal_id)
            except Sucursal.DoesNotExist:
                pass
        return None
    
    # Para usuarios normales, primero intentar sucursal asignada
    if hasattr(request.user, 'sucursal') and request.user.sucursal:
        return request.user.sucursal
    
    # Si no tiene sucursal asignada, intentar de sesión
    sucursal_id = request.session.get('sucursal_actual')
    if sucursal_id:
        try:
            return Sucursal.objects.get(id=sucursal_id)
        except Sucursal.DoesNotExist:
            pass
    
    # Si no hay nada, redirigir a seleccionar
    messages.warning(request, 'No tienes una sucursal asignada. Contacta al administrador.')
    return redirect('sucursales:seleccionar')


# ===============================
# FACTURACIÓN
# ===============================

@login_required
def ver_factura_completa(request, factura_id):
    """Ver factura completa con todos los detalles legales"""
    factura = get_object_or_404(
        Factura.objects.select_related('sucursal', 'usuario', 'cliente'),
        id=factura_id
    )
    
    # Verificar permisos
    sucursal = obtener_sucursal_usuario(request)
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        from django.http import HttpResponseRedirect
        if isinstance(sucursal, HttpResponseRedirect):
            return sucursal
        if factura.sucursal != sucursal:
            messages.error(request, 'No tienes permiso para ver esta factura')
            return redirect('facturas:lista_facturas')
    
    detalles = factura.detalles.select_related('producto', 'producto__categoria').all()
    
    return render(request, 'facturas/ver_factura.html', {
        'factura': factura,
        'detalles': detalles,
    })


@login_required
def imprimir_factura(request, factura_id):
    """Vista de impresión formato POS térmico 80mm"""
    factura = get_object_or_404(
        Factura.objects.select_related('sucursal', 'usuario', 'cliente'),
        id=factura_id
    )
    
    detalles = factura.detalles.select_related('producto').all()
    
    return render(request, 'facturas/imprimir.html', {
        'factura': factura,
        'detalles': detalles,
    })


@login_required
def lista_facturas(request):
    """Lista todas las facturas"""
    sucursal = obtener_sucursal_usuario(request)
    from django.http import HttpResponseRedirect
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    # Filtrar por sucursal
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        facturas = Factura.objects.all()
    else:
        facturas = Factura.objects.filter(sucursal=sucursal)
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cliente_id = request.GET.get('cliente')
    numero_factura = request.GET.get('numero_factura', '').strip()
    
    if fecha_desde:
        facturas = facturas.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        facturas = facturas.filter(fecha__lte=fecha_hasta)
    if cliente_id:
        facturas = facturas.filter(cliente_id=cliente_id)
    if numero_factura:
        facturas = facturas.filter(numero_factura__icontains=numero_factura)
    
    facturas = facturas.select_related('cliente', 'usuario', 'sucursal').order_by('-fecha')[:100]
    
    # Estadísticas
    stats = facturas.aggregate(
        total_facturas=Count('id'),
        total_ventas=Sum('total'),
        total_anuladas=Count('id', filter=Q(anulada=True))
    )
    
    clientes = Cliente.objects.filter(activo=True).order_by('nombre_completo')[:50]
    
    return render(request, 'facturas/lista.html', {
        'facturas': facturas,
        'stats': stats,
        'sucursal': sucursal,
        'clientes': clientes,
    })


@login_required
def anular_factura(request, factura_id):
    """Anular factura y devolver inventario"""
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Verificar permisos
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ No tienes permisos para anular facturas')
        return redirect('facturas:ver_factura_completa', factura_id)
    
    if factura.anulada:
        messages.warning(request, '⚠️ Esta factura ya está anulada')
        return redirect('facturas:ver_factura_completa', factura_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        if not motivo:
            messages.error(request, '❌ Debes especificar el motivo de anulación')
            return redirect('facturas:anular_factura', factura_id)
        
        try:
            with transaction.atomic():
                # Devolver inventario
                for detalle in factura.detalles.all():
                    inventario = InventarioSucursal.objects.get(
                        producto=detalle.producto,
                        sucursal=factura.sucursal
                    )
                    inventario.cantidad += detalle.cantidad
                    inventario.save()
                    
                    # Registrar movimiento de devolución
                    MovimientoInventario.objects.create(
                        producto=detalle.producto,
                        sucursal=factura.sucursal,
                        tipo='ENTRADA',
                        cantidad=detalle.cantidad,
                        motivo='DEVOLUCION',
                        usuario=request.user,
                        factura=factura,
                        observaciones=f'Anulación factura {factura.numero_factura}: {motivo}'
                    )
                
                # Marcar factura como anulada
                factura.anulada = True
                factura.motivo_anulacion = motivo
                factura.save()
                
                registrar_actividad(
                    request.user,
                    tipo='ANULACION',
                    descripcion=f'Anuló factura {factura.numero_factura}: {motivo}',
                    request=request
                )
                
                messages.success(request, f'✅ Factura {factura.numero_factura} anulada correctamente')
                return redirect('facturas:ver_factura_completa', factura_id)
                
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return render(request, 'facturas/anular.html', {'factura': factura})


@login_required
def buscar_cliente_ajax(request):
    """AJAX: Buscar cliente por documento"""
    documento = request.GET.get('documento', '').strip()
    
    if not documento:
        return JsonResponse({'encontrado': False})
    
    try:
        cliente = Cliente.objects.get(numero_documento=documento, activo=True)
        return JsonResponse({
            'encontrado': True,
            'cliente': {
                'id': cliente.id,
                'nombre_completo': cliente.nombre_completo,
                'tipo_documento': cliente.tipo_documento,
                'numero_documento': cliente.numero_documento,
                'email': cliente.email,
                'telefono': cliente.telefono,
                'direccion': cliente.direccion,
                'ciudad': cliente.ciudad,
            }
        })
    except Cliente.DoesNotExist:
        return JsonResponse({'encontrado': False})


# ===============================
# GESTIÓN DE CLIENTES
# ===============================

@login_required
def lista_clientes(request):
    """Lista todos los clientes"""
    clientes = Cliente.objects.filter(activo=True).order_by('nombre_completo')
    
    # Búsqueda
    busqueda = request.GET.get('q', '')
    if busqueda:
        clientes = clientes.filter(
            Q(nombre_completo__icontains=busqueda) |
            Q(numero_documento__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    return render(request, 'facturas/clientes/lista.html', {
        'clientes': clientes,
        'busqueda': busqueda,
    })


@login_required
def crear_cliente(request):
    """Crear nuevo cliente"""
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.create(
                tipo_documento=request.POST.get('tipo_documento'),
                numero_documento=request.POST.get('numero_documento'),
                nombre_completo=request.POST.get('nombre_completo'),
                email=request.POST.get('email', ''),
                telefono=request.POST.get('telefono', ''),
                direccion=request.POST.get('direccion', ''),
                ciudad=request.POST.get('ciudad', '')
            )
            
            messages.success(request, f'✅ Cliente {cliente.nombre_completo} creado correctamente')
            return redirect('facturas:lista_clientes')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return render(request, 'facturas/clientes/crear.html')


@login_required
def editar_cliente(request, cliente_id):
    """Editar cliente existente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        try:
            cliente.tipo_documento = request.POST.get('tipo_documento')
            cliente.numero_documento = request.POST.get('numero_documento')
            cliente.nombre_completo = request.POST.get('nombre_completo')
            cliente.email = request.POST.get('email', '')
            cliente.telefono = request.POST.get('telefono', '')
            cliente.direccion = request.POST.get('direccion', '')
            cliente.ciudad = request.POST.get('ciudad', '')
            cliente.save()
            
            messages.success(request, f'✅ Cliente actualizado correctamente')
            return redirect('facturas:lista_clientes')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return render(request, 'facturas/clientes/editar.html', {'cliente': cliente})