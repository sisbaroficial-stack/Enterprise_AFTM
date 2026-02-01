from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone

from .models import Sucursal
from inventario.models import Producto, InventarioSucursal, TransferenciaSucursal, MovimientoInventario
from usuarios.models import Usuario

from django.db.models import Q, F

from usuarios.views import registrar_actividad


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect


def es_admin(user):
    return user.is_authenticated and user.rol in ['ADMIN', 'SUPER_ADMIN']


@login_required
def seleccionar_sucursal(request):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN']:
        return HttpResponseForbidden("No tienes permisos")
    """Seleccionar sucursal para trabajar"""
    sucursales = Sucursal.objects.filter(activa=True)
    
    context = {
        'sucursales': sucursales
    }
    return render(request, 'sucursales/seleccionar.html', context)


@login_required
def establecer_sucursal(request, sucursal_id):
    """Establecer sucursal activa en la sesión"""
    sucursal = get_object_or_404(Sucursal, id=sucursal_id, activa=True)
    request.session['sucursal_actual'] = sucursal_id
    messages.success(request, f'Trabajando en: {sucursal.nombre}')
    return redirect('dashboard:home')


@login_required
def inventario_sucursal(request):
    """Ver inventario de la sucursal actual"""
    sucursal_id = request.session.get('sucursal_actual')
    
    if not sucursal_id:
        return redirect('sucursales:seleccionar')
    
    sucursal = get_object_or_404(Sucursal, id=sucursal_id)
    inventarios = InventarioSucursal.objects.filter(
        sucursal=sucursal
    ).select_related('producto', 'producto__categoria')
    
    # Filtros
    busqueda = request.GET.get('q', '')
    if busqueda:
        inventarios = inventarios.filter(
            Q(producto__nombre__icontains=busqueda) |
            Q(producto__codigo__icontains=busqueda)
        )
    
    # Estadísticas
    stats = {
        'total_productos': inventarios.count(),
        'agotados': inventarios.filter(cantidad=0).count(),
        'por_agotar': inventarios.filter(
            cantidad__lte=F('cantidad_minima'),
            cantidad__gt=0
        ).count(),
    }
    
    context = {
        'sucursal': sucursal,
        'inventarios': inventarios,
        'stats': stats,
        'busqueda': busqueda,
    }
    return render(request, 'sucursales/inventario.html', context)


@login_required
def crear_transferencia(request):
    """Crear transferencias múltiples entre sucursales"""
    
    # Verificar permisos
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN', 'EMPLEADO']:
        messages.error(request, '⛔ No tienes permisos para crear transferencias')
        return redirect('dashboard:home')
    
    # Determinar sucursal origen
    sucursal_origen = None
    
    if request.user.rol == 'SUPER_ADMIN':
        sucursal_id = request.session.get('sucursal_actual')
        if not sucursal_id:
            messages.warning(request, 'Selecciona una sucursal primero')
            return redirect('sucursales:seleccionar')
        sucursal_origen = get_object_or_404(Sucursal, id=sucursal_id)
    else:
        if hasattr(request.user, 'sucursal') and request.user.sucursal:
            sucursal_origen = request.user.sucursal
        else:
            messages.error(request, '⛔ No tienes una sucursal asignada')
            return redirect('dashboard:home')
    
    if request.method == 'POST':
        import json
        
        try:
            carrito_json = request.POST.get('carrito', '[]')
            carrito = json.loads(carrito_json)
            sucursal_destino_id = request.POST.get('sucursal_destino')
            motivo = request.POST.get('motivo', '')
            
            if not carrito or len(carrito) == 0:
                messages.error(request, '❌ El carrito está vacío')
                return redirect('sucursales:crear_transferencia')
            
            if not sucursal_destino_id:
                messages.error(request, '❌ Debes seleccionar una sucursal de destino')
                return redirect('sucursales:crear_transferencia')
            
            sucursal_destino = get_object_or_404(Sucursal, id=sucursal_destino_id)
            
            # Procesar cada producto del carrito
            transferencias_creadas = []
            
            from django.db import transaction
            with transaction.atomic():
                for item in carrito:
                    producto_id = item['id']
                    cantidad = int(item['cantidad'])
                    
                    producto = get_object_or_404(Producto, id=producto_id)
                    
                    # Verificar stock
                    inv_origen = InventarioSucursal.objects.get(
                        producto=producto,
                        sucursal=sucursal_origen
                    )
                    
                    if inv_origen.cantidad < cantidad:
                        raise ValueError(
                            f'Stock insuficiente para {producto.nombre}. '
                            f'Disponible: {inv_origen.cantidad}'
                        )
                    
                    # Descontar de origen
                    inv_origen.cantidad -= cantidad
                    inv_origen.save()
                    
                    # Crear transferencia
                    transferencia = TransferenciaSucursal.objects.create(
                        producto=producto,
                        sucursal_origen=sucursal_origen,
                        sucursal_destino=sucursal_destino,
                        cantidad=cantidad,
                        motivo=motivo,
                        solicitado_por=request.user,
                        aprobado_por=request.user,
                        estado='EN_TRANSITO',
                        fecha_envio=timezone.now()
                    )
                    
                    # Registrar movimiento
                    MovimientoInventario.objects.create(
                        producto=producto,
                        sucursal=sucursal_origen,
                        tipo='SALIDA',
                        cantidad=cantidad,
                        motivo='TRANSFERENCIA',
                        usuario=request.user,
                        observaciones=f'Transferencia a {sucursal_destino.nombre} ({transferencia.codigo})'
                    )
                    
                    transferencias_creadas.append(transferencia.codigo)
                
                registrar_actividad(
                    request.user,
                    tipo='TRANSFERENCIA',
                    descripcion=f'Creó {len(carrito)} transferencias hacia {sucursal_destino.nombre}',
                    request=request
                )
                
                messages.success(
                    request,
                    f'✅ {len(transferencias_creadas)} transferencia(s) enviada(s) exitosamente'
                )
                return redirect('sucursales:lista_transferencias')
                
        except ValueError as e:
            messages.error(request, f'❌ {str(e)}')
            return redirect('sucursales:crear_transferencia')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('sucursales:crear_transferencia')
    
    # GET
    inventarios = InventarioSucursal.objects.filter(
        sucursal=sucursal_origen,
        cantidad__gt=0
    ).select_related('producto', 'producto__categoria').order_by('producto__nombre')
    
    sucursales_destino = Sucursal.objects.filter(
        activa=True
    ).exclude(id=sucursal_origen.id)
    
    context = {
        'sucursal_origen': sucursal_origen,
        'inventarios': inventarios,
        'sucursales_destino': sucursales_destino,
    }
    return render(request, 'sucursales/crear_transferencia.html', context)

@login_required
def lista_transferencias(request):
    """
    Lista todas las transferencias.
    - SUPER_ADMIN: Si tiene sucursal en sesión, filtra por esa sucursal. Si no, ve todas.
    - ADMIN: Solo ve transferencias de su sucursal asignada (igual que EMPLEADO)
    - EMPLEADO: Solo ve transferencias de su sucursal asignada
    """
    estado_filtro = request.GET.get('estado', '').upper()
    sucursal = None
    
    if request.user.rol == 'SUPER_ADMIN':
        # ✅ SUPER_ADMIN: Verificar si tiene sucursal seleccionada
        sucursal_id = request.session.get('sucursal_actual')
        
        if sucursal_id:
            # Tiene sucursal seleccionada → Filtrar por esa sucursal
            sucursal = get_object_or_404(Sucursal, id=sucursal_id)
            transferencias = TransferenciaSucursal.objects.filter(
                sucursal_destino=sucursal
            )
        else:
            # No tiene sucursal seleccionada → Ve todas
            transferencias = TransferenciaSucursal.objects.all()
    
    else:
        # ✅ ADMIN y EMPLEADO: Solo ven transferencias de su sucursal asignada
        if hasattr(request.user, 'sucursal') and request.user.sucursal:
            sucursal = request.user.sucursal
        else:
            messages.error(request, '⛔ No tienes una sucursal asignada. Contacta al administrador.')
            return redirect('usuarios:dashboard')
        
        # Filtrar transferencias donde la sucursal sea destino (para recibir)
        transferencias = TransferenciaSucursal.objects.filter(
            sucursal_destino=sucursal
        )
    
    # Aplicar filtro por estado
    if estado_filtro:
        transferencias = transferencias.filter(estado=estado_filtro)
    
    # Ordenar
    transferencias = transferencias.select_related(
        'producto', 
        'sucursal_origen', 
        'sucursal_destino',
        'solicitado_por',
        'recibido_por'
    ).order_by('-fecha_solicitud')
    
    return render(request, 'sucursales/lista_transferencias.html', {
        'transferencias': transferencias,
        'sucursal': sucursal,
        'estado_filtro': estado_filtro
    })

@login_required
def recibir_transferencia(request, transferencia_id):
    """Recibir transferencia - Disponible para ADMIN, SUPER_ADMIN y EMPLEADO"""
    transferencia = get_object_or_404(TransferenciaSucursal, id=transferencia_id)
    
    # Verificar que el usuario tenga permisos en la sucursal destino
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        # EMPLEADO: verificar que sea de su sucursal
        sucursal_usuario = None
        if hasattr(request.user, 'sucursal') and request.user.sucursal:
            sucursal_usuario = request.user.sucursal
        elif request.session.get('sucursal_actual'):
            sucursal_usuario = get_object_or_404(Sucursal, id=request.session.get('sucursal_actual'))
        
        if not sucursal_usuario or transferencia.sucursal_destino != sucursal_usuario:
            messages.error(request, '⛔ No puedes recibir esta transferencia')
            return redirect('sucursales:lista_transferencias')
    
    try:
        transferencia.recibir_transferencia(request.user)
        messages.success(request, f'✅ Transferencia {transferencia.codigo} recibida correctamente')
    except ValueError as e:
        messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('sucursales:lista_transferencias')

@login_required
@user_passes_test(es_admin)
def gestionar_sucursales(request):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos")
    """Gestionar sucursales (CRUD)"""
    sucursales = Sucursal.objects.all().select_related('encargado')
    
    context = {
        'sucursales': sucursales
    }
    return render(request, 'sucursales/gestionar.html', context)


@login_required
@user_passes_test(es_admin)
def crear_sucursal_view(request):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN']:
        return HttpResponseForbidden("No tienes permisos")
    """Crear nueva sucursal"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo')
        tipo = request.POST.get('tipo')
        direccion = request.POST.get('direccion', '')
        telefono = request.POST.get('telefono', '')
        encargado_id = request.POST.get('encargado')
        es_principal = request.POST.get('es_principal') == 'on'
        
        try:
            encargado = Usuario.objects.get(id=encargado_id) if encargado_id else None
            
            sucursal = Sucursal.objects.create(
                nombre=nombre,
                codigo=codigo,
                tipo=tipo,
                direccion=direccion,
                telefono=telefono,
                encargado=encargado,
                es_principal=es_principal
            )
            
            messages.success(request, f'Sucursal {sucursal.nombre} creada correctamente')
            return redirect('sucursales:gestionar')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    usuarios = Usuario.objects.filter(is_active=True, rol__in=['ADMIN', 'EMPLEADO'])
    
    context = {
        'usuarios': usuarios
    }
    return render(request, 'sucursales/crear.html', context)


@login_required
@user_passes_test(es_admin)
def editar_sucursal_view(request, sucursal_id):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN']:
        return HttpResponseForbidden("No tienes permisos")
    """Editar sucursal"""
    sucursal = get_object_or_404(Sucursal, id=sucursal_id)
    
    if request.method == 'POST':
        sucursal.nombre = request.POST.get('nombre')
        sucursal.codigo = request.POST.get('codigo')
        sucursal.tipo = request.POST.get('tipo')
        sucursal.direccion = request.POST.get('direccion', '')
        sucursal.telefono = request.POST.get('telefono', '')
        sucursal.activa = request.POST.get('activa') == 'on'
        sucursal.es_principal = request.POST.get('es_principal') == 'on'
        
        encargado_id = request.POST.get('encargado')
        sucursal.encargado = Usuario.objects.get(id=encargado_id) if encargado_id else None
        
        sucursal.save()
        
        messages.success(request, f'Sucursal {sucursal.nombre} actualizada')
        return redirect('sucursales:gestionar')
    
    usuarios = Usuario.objects.filter(is_active=True, rol__in=['ADMIN', 'EMPLEADO'])
    
    context = {
        'sucursal': sucursal,
        'usuarios': usuarios
    }
    return render(request, 'sucursales/editar.html', context)


@login_required
def crear(request):
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, 'No tienes permisos para crear sucursales')
        return redirect('sucursales:gestionar')


@login_required
def establecer_todas_sucursales(request):
    """Permite al SUPER_ADMIN ver todas las sucursales (modo global)"""
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ No tienes permisos para ver todas las sucursales')
        return redirect('sucursales:seleccionar')
    
    # Limpiar la sucursal de sesión para ver todo
    if 'sucursal_actual' in request.session:
        del request.session['sucursal_actual']
    
    messages.success(request, '🌍 Modo Global Activado: Viendo todas las sucursales')
    return redirect('inventario:listar_productos')