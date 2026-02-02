from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F, Sum
from django.http import JsonResponse
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect


from .models import Producto, Categoria, MovimientoInventario, InventarioSucursal, AlertaInventario
from sucursales.models import Sucursal
from .forms import ProductoForm
from usuarios.views import registrar_actividad


# ===============================
# HELPERS
# ===============================
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
        # SUPER_ADMIN puede trabajar sin sucursal
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
# LISTAR PRODUCTOS
# ===============================
# ===============================
# LISTAR PRODUCTOS
# ===============================
@login_required
def lista_productos(request):
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal

    # SUPER_ADMIN sin sucursal seleccionada = ve todos los productos
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        productos = Producto.objects.filter(activo=True).select_related('categoria')
    elif request.user.rol == 'SUPER_ADMIN' and sucursal:
        # SUPER_ADMIN con sucursal seleccionada = ve solo esa sucursal
        productos = Producto.objects.filter(
            inventarios__sucursal=sucursal,
            activo=True
        ).select_related('categoria').distinct()
    else:
        # Usuarios normales solo ven su sucursal
        productos = Producto.objects.filter(
            inventarios__sucursal=sucursal,
            activo=True
        ).select_related('categoria').distinct()

    # === FILTROS ===
    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(codigo__icontains=busqueda) |
            Q(codigo_barras__icontains=busqueda)
        )
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # === CALCULAR STOCK Y ESTADO POR PRODUCTO ===
    productos_con_stock = []
    for p in productos:
        if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
            # Mostrar stock total de todas las sucursales
            total_cantidad = p.inventarios.aggregate(total=Sum('cantidad'))['total'] or 0
            min_cantidad = p.inventarios.aggregate(total=Sum('cantidad_minima'))['total'] or 0
        else:
            # Mostrar stock de la sucursal específica
            total_cantidad = p.inventarios.filter(sucursal=sucursal).aggregate(total=Sum('cantidad'))['total'] or 0
            min_cantidad = p.inventarios.filter(sucursal=sucursal).aggregate(total=Sum('cantidad_minima'))['total'] or 0
        
        # Determinar estado
        if total_cantidad == 0:
            estado = 'AGOTADO'
        elif total_cantidad <= min_cantidad:
            estado = 'POR_AGOTAR'
        else:
            estado = 'DISPONIBLE'
        
        # Agregar a la lista
        productos_con_stock.append({
            'producto': p,
            'total_cantidad': total_cantidad,
            'min_cantidad': min_cantidad,
            'estado': estado,
        })

    # === FILTRAR POR ESTADO (después de calcular) ===
    if estado_filtro:
        productos_con_stock = [
            item for item in productos_con_stock 
            if item['estado'] == estado_filtro
        ]

    # === ESTADÍSTICAS ===
    stats = {
        'total': len(productos_con_stock),
        'disponibles': sum(1 for i in productos_con_stock if i['estado'] == 'DISPONIBLE'),
        'por_agotar': sum(1 for i in productos_con_stock if i['estado'] == 'POR_AGOTAR'),
        'agotados': sum(1 for i in productos_con_stock if i['estado'] == 'AGOTADO'),
    }

    categorias = Categoria.objects.filter(activa=True)

    return render(request, 'inventario/listar_productos.html', {
        'productos_con_stock': productos_con_stock,
        'categorias': categorias,
        'stats': stats,
        'busqueda': busqueda,
        'categoria_filtro': categoria_id,
        'estado_filtro': estado_filtro,
        'sucursal': sucursal,
    })

# ===============================
# CREAR PRODUCTO
# ===============================
@login_required
def crear_producto(request):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para crear productos")

    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    producto = form.save(commit=False)
                    producto.creado_por = request.user
                    producto.save()

                    cantidad_inicial = int(request.POST.get('cantidad_inicial', 0))

                    # Solo crear inventario si hay sucursal
                    if sucursal:
                        InventarioSucursal.objects.create(
                            producto=producto,
                            sucursal=sucursal,
                            cantidad=cantidad_inicial,
                            cantidad_minima=producto.cantidad_minima,
                            ubicacion=request.POST.get('ubicacion', '')
                        )
                    elif request.user.rol == 'SUPER_ADMIN':
                        # SUPER_ADMIN sin sucursal: crear inventario en todas las sucursales
                        sucursales = Sucursal.objects.filter(activa=True)
                        for suc in sucursales:
                            InventarioSucursal.objects.create(
                                producto=producto,
                                sucursal=suc,
                                cantidad=0,
                                cantidad_minima=producto.cantidad_minima,
                                ubicacion=''
                            )

                    registrar_actividad(
                        request.user,
                        tipo='INVENTARIO',
                        descripcion=f'Creó producto {producto.nombre}',
                        request=request
                    )

                    messages.success(request, 'Producto creado correctamente')
                    return redirect('inventario:listar_productos')
            except Exception as e:
                messages.error(request, f'Error al crear producto: {e}')
        else:
            messages.error(request, 'Formulario inválido')
    else:
        form = ProductoForm()

    return render(request, 'inventario/crear_producto.html', {
        'form': form,
        'sucursal': sucursal,
        'titulo': 'Crear Producto'
    })

# ===============================
# EDITAR PRODUCTO
# ===============================
@login_required
def editar_producto(request, producto_id):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para editar productos")

    

    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal

    producto = get_object_or_404(Producto, id=producto_id)
    
    # Obtener inventario según el rol
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        # SUPER_ADMIN sin sucursal ve el primer inventario disponible
        inventario = InventarioSucursal.objects.filter(producto=producto).first()
    else:
        # Otros roles o SUPER_ADMIN con sucursal seleccionada
        try:
            inventario = InventarioSucursal.objects.get(
                producto=producto,
                sucursal=sucursal
            )
        except InventarioSucursal.DoesNotExist:
            inventario = None

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            
            # Actualizar inventario si existe
            if inventario:
                inventario.cantidad_minima = producto.cantidad_minima
                inventario.ubicacion = request.POST.get('ubicacion', inventario.ubicacion)
                inventario.save()
            
            registrar_actividad(
                request.user,
                tipo='INVENTARIO',
                descripcion=f'Editó producto {producto.nombre}',
                request=request
            )
            messages.success(request, 'Producto actualizado correctamente')
            return redirect('inventario:listar_productos')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/crear_producto.html', {
        'form': form,
        'producto': producto,
        'inventario': inventario,
        'sucursal': sucursal,
        'titulo': 'Editar Producto'
    })

# ===============================
# DESCONTAR STOCK
# ===============================
@login_required
def descontar_producto(request, producto_id):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para descontar productos")

    
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    # SUPER_ADMIN sin sucursal debe seleccionar una
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        messages.warning(request, 'Por favor selecciona una sucursal para descontar stock')
        return redirect('sucursales:seleccionar')
    
    # Buscar el inventario en la sucursal
    try:
        inventario = InventarioSucursal.objects.get(
            producto_id=producto_id,
            sucursal=sucursal
        )
    except InventarioSucursal.DoesNotExist:
        messages.error(request, 'Este producto no existe en tu sucursal')
        return redirect('inventario:listar_productos')

    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 0))
            motivo = request.POST.get('motivo', 'VENTA')
            observaciones = request.POST.get('observaciones', '')

            if cantidad <= 0:
                messages.error(request, 'La cantidad debe ser mayor a cero')
                return redirect('inventario:descontar_producto', producto_id)
            
            if cantidad > inventario.cantidad:
                messages.error(request, f'Stock insuficiente. Disponible: {inventario.cantidad}')
                return redirect('inventario:descontar_producto', producto_id)

            inventario.cantidad -= cantidad
            inventario.save()

            MovimientoInventario.objects.create(
                producto=inventario.producto,
                sucursal=sucursal,
                tipo='SALIDA',
                cantidad=cantidad,
                motivo=motivo,
                usuario=request.user,
                observaciones=f'{observaciones} - {sucursal.nombre}'
            )

            registrar_actividad(
                request.user,
                tipo='INVENTARIO',
                descripcion=f'Descontó {cantidad} de {inventario.producto.nombre}',
                request=request
            )

            messages.success(request, f'Se descontaron {cantidad} unidades del stock')
            return redirect('inventario:listar_productos')
            
        except ValueError:
            messages.error(request, 'Cantidad inválida')
            return redirect('inventario:descontar_producto', producto_id)
        except Exception as e:
            messages.error(request, f'Error al descontar stock: {str(e)}')
            return redirect('inventario:descontar_producto', producto_id)

    return render(request, 'inventario/descontar_producto.html', {
        'producto': inventario.producto,
        'inventario': inventario,
        'sucursal': sucursal,
    })


# ===============================
# AGREGAR STOCK
# ===============================
@login_required
def agregar_stock(request, producto_id):
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    # SUPER_ADMIN sin sucursal debe seleccionar una
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        messages.warning(request, 'Por favor selecciona una sucursal para agregar stock')
        return redirect('sucursales:seleccionar')
    
    # Obtener o crear el inventario
    try:
        inventario, created = InventarioSucursal.objects.get_or_create(
            producto_id=producto_id,
            sucursal=sucursal,
            defaults={'cantidad': 0}
        )
    except Exception as e:
        messages.error(request, f'Error al acceder al inventario: {str(e)}')
        return redirect('inventario:listar_productos')
    
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 0))
            if cantidad <= 0:
                messages.error(request, 'La cantidad debe ser mayor a cero')
                return redirect('inventario:agregar_stock', producto_id)
            
            inventario.cantidad += cantidad
            inventario.save()
            
            MovimientoInventario.objects.create(
                producto=inventario.producto,
                sucursal=sucursal,
                tipo='ENTRADA',
                cantidad=cantidad,
                motivo='COMPRA',
                usuario=request.user,
                observaciones=f'Ingreso manual - {sucursal.nombre}'
            )
            
            registrar_actividad(
                request.user,
                tipo='INVENTARIO',
                descripcion=f'Agregó {cantidad} unidades a {inventario.producto.nombre}',
                request=request
            )
            
            messages.success(request, f'Se agregaron {cantidad} unidades al stock correctamente')
            return redirect('inventario:listar_productos')
            
        except ValueError:
            messages.error(request, 'Cantidad inválida')
            return redirect('inventario:agregar_stock', producto_id)
        except Exception as e:
            messages.error(request, f'Error al agregar stock: {str(e)}')
            return redirect('inventario:agregar_stock', producto_id)
    
    return render(request, 'inventario/agregar_stock.html', {
        'producto': inventario.producto,
        'inventario': inventario,
        'sucursal': sucursal,
    })
# ===============================
# DETALLE PRODUCTO
# ===============================
@login_required
def detalle_producto(request, producto_id):
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        # SUPER_ADMIN sin sucursal ve todos los inventarios
        inventario = InventarioSucursal.objects.filter(producto=producto).first()
        movimientos = MovimientoInventario.objects.filter(producto=producto).order_by('-fecha')[:20]
        otros_inventarios = InventarioSucursal.objects.filter(producto=producto).select_related('sucursal')
    else:
        # Usuarios normales o SUPER_ADMIN con sucursal
        try:
            inventario = InventarioSucursal.objects.get(
                producto=producto,
                sucursal=sucursal
            )
        except InventarioSucursal.DoesNotExist:
            messages.error(request, 'Este producto no existe en tu sucursal')
            return redirect('inventario:listar_productos')
        
        movimientos = MovimientoInventario.objects.filter(
            producto=producto,
            sucursal=sucursal
        ).order_by('-fecha')[:20]
        otros_inventarios = InventarioSucursal.objects.filter(
            producto=producto
        ).exclude(sucursal=sucursal).select_related('sucursal')
    
    # Calcular estado basado en el inventario actual
    if inventario:
        cantidad_actual = inventario.cantidad
        cantidad_minima = inventario.cantidad_minima
        
        if cantidad_actual == 0:
            estado_display = 'Agotado'
            estado_color = 'danger'
            estado_icono = 'x-circle'
        elif cantidad_actual <= cantidad_minima:
            estado_display = 'Stock Bajo'
            estado_color = 'warning'
            estado_icono = 'exclamation-triangle'
        else:
            estado_display = 'Disponible'
            estado_color = 'success'
            estado_icono = 'check-circle'
    else:
        cantidad_actual = 0
        cantidad_minima = 0
        estado_display = 'Sin inventario'
        estado_color = 'secondary'
        estado_icono = 'info-circle'
    
    return render(request, 'inventario/ver_producto.html', {
        'producto': producto,
        'inventario': inventario,
        'cantidad_actual': cantidad_actual,
        'cantidad_minima': cantidad_minima,
        'estado_display': estado_display,
        'estado_color': estado_color,
        'estado_icono': estado_icono,
        'movimientos': movimientos,
        'otros_inventarios': otros_inventarios,
        'sucursal': sucursal,
    })
# ===============================
# ELIMINAR PRODUCTO
# ===============================
@login_required
def eliminar_producto(request, producto_id):
    

    # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para eliminar productos")
    
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    # SUPER_ADMIN sin sucursal puede eliminar directamente
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        producto.activo = False
        producto.save()
        
        registrar_actividad(
            request.user,
            tipo='INVENTARIO',
            descripcion=f'Eliminó producto {producto.nombre} (global)',
            request=request
        )
        
        messages.success(request, 'Producto eliminado correctamente')
        return redirect('inventario:listar_productos')
    
    # Para otros usuarios, verificar que exista en su sucursal
    try:
        inventario = InventarioSucursal.objects.get(
            producto_id=producto_id,
            sucursal=sucursal
        )
        producto.activo = False
        producto.save()
        
        registrar_actividad(
            request.user,
            tipo='INVENTARIO',
            descripcion=f'Eliminó producto {producto.nombre}',
            request=request
        )
        
        messages.success(request, 'Producto eliminado correctamente')
    except InventarioSucursal.DoesNotExist:
        messages.error(request, 'Este producto no existe en tu sucursal')
    
    return redirect('inventario:listar_productos')

# ===============================
# AJAX BUSCAR PRODUCTO
# ===============================
@login_required
def buscar_producto_ajax(request):
    codigo = request.GET.get('codigo', '').strip()
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, redirect) or not codigo:
        return JsonResponse({'encontrado': False})

    try:
        inventario = InventarioSucursal.objects.select_related('producto').get(
            sucursal=sucursal,
            producto__codigo=codigo
        )
        p = inventario.producto
        return JsonResponse({
            'encontrado': True,
            'producto': {
                'nombre': p.nombre,
                'codigo': p.codigo,
                'categoria': p.categoria.nombre,
                'cantidad': inventario.cantidad,
                'unidad_medida': p.unidad_medida,
                'estado': inventario.estado,
            }
        })
    except InventarioSucursal.DoesNotExist:
        return JsonResponse({'encontrado': False})


# ===============================
# LISTAR MOVIMIENTOS
# ===============================
@login_required
def listar_movimientos(request):
    dias = int(request.GET.get('dias', 7))
    fecha_limite = timezone.now() - timedelta(days=dias)

    if request.user.rol in ['ADMIN', 'SUPER_ADMIN']:
        movimientos = MovimientoInventario.objects.filter(
            fecha__gte=fecha_limite
        ).select_related('producto', 'usuario', 'sucursal').order_by('-fecha')
    else:
        sucursal = obtener_sucursal_usuario(request)
        if isinstance(sucursal, HttpResponseRedirect):

            return sucursal
        movimientos = MovimientoInventario.objects.filter(
            fecha__gte=fecha_limite,
            sucursal=sucursal
        ).select_related('producto', 'usuario', 'sucursal').order_by('-fecha')

    return render(request, 'movimientos/listar.html', {
        'movimientos': movimientos,
        'dias': dias,
    })


# ===============================
# PANEL INVENTARIO
# ===============================
@login_required
def panel_inventario(request):
    dias = int(request.GET.get('dias', 7))
    fecha_inicio = timezone.now() - timedelta(days=dias)

    if request.user.rol in ['ADMIN', 'SUPER_ADMIN']:
        movimientos = MovimientoInventario.objects.filter(
            fecha__gte=fecha_inicio
        ).select_related('producto', 'usuario', 'sucursal').order_by('-fecha')
        alertas = AlertaInventario.objects.all().order_by('-fecha_generada')
    else:
        sucursal = obtener_sucursal_usuario(request)
        if isinstance(sucursal, HttpResponseRedirect):

            return sucursal
        movimientos = MovimientoInventario.objects.filter(
            fecha__gte=fecha_inicio,
            sucursal=sucursal
        ).select_related('producto', 'usuario').order_by('-fecha')
        alertas = AlertaInventario.objects.filter(
            producto__inventariosucursal__sucursal=sucursal
        ).order_by('-fecha_generada')

    return render(request, 'inventario/panel_inventario.html', {
        'movimientos': movimientos,
        'alertas': alertas,
        'dias': dias
    })
@login_required
def venta_rapida(request):
    """Vista para descuento rápido de productos (ventas)"""
    # Obtener sucursal del usuario (obligatoria para esta acción)
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    # SUPER_ADMIN sin sucursal debe seleccionar una
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        messages.warning(request, '⚠️ Debes seleccionar una sucursal para realizar ventas')
        return redirect('sucursales:seleccionar')
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        cantidad_str = request.POST.get('cantidad', '1')
        
        try:
            cantidad = int(cantidad_str)
            if cantidad <= 0:
                messages.error(request, '❌ La cantidad debe ser mayor a cero')
                return redirect('inventario:venta_rapida')
            
            # Buscar producto por código o código de barras
            inventario = InventarioSucursal.objects.select_related('producto').filter(
                Q(producto__codigo=codigo) | Q(producto__codigo_barras=codigo),
                sucursal=sucursal,
                producto__activo=True
            ).first()
            
            if not inventario:
                messages.error(request, f'❌ Producto con código "{codigo}" no encontrado en esta sucursal')
                return redirect('inventario:venta_rapida')
            
            # Verificar stock
            if inventario.cantidad < cantidad:
                messages.error(
                    request,
                    f'❌ Stock insuficiente. Disponible: {inventario.cantidad} {inventario.producto.unidad_medida}'
                )
                return redirect('inventario:venta_rapida')
            
            # Descontar stock
            inventario.cantidad -= cantidad
            inventario.save()
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                producto=inventario.producto,
                sucursal=sucursal,
                tipo='SALIDA',
                cantidad=cantidad,
                motivo='VENTA',
                usuario=request.user,
                observaciones=f'Venta rápida - {sucursal.nombre}'
            )
            
            # Registrar actividad
            registrar_actividad(
                request.user,
                tipo='DESCONTAR',
                descripcion=f'Venta rápida: {cantidad} {inventario.producto.unidad_medida} de {inventario.producto.nombre}',
                request=request
            )
            
            messages.success(
                request,
                f'✅ Venta registrada: {cantidad} {inventario.producto.unidad_medida} de {inventario.producto.nombre}'
            )
            return redirect('inventario:venta_rapida')
            
        except ValueError:
            messages.error(request, '❌ Cantidad inválida')
            return redirect('inventario:venta_rapida')
        except Exception as e:
            messages.error(request, f'❌ Error al procesar venta: {str(e)}')
            return redirect('inventario:venta_rapida')
    
    # GET - Obtener productos recientes para referencia
    productos_recientes = InventarioSucursal.objects.filter(
        sucursal=sucursal,
        producto__activo=True,
        cantidad__gt=0
    ).select_related('producto', 'producto__categoria').order_by('-producto__id')[:15]
    
    return render(request, 'inventario/venta_rapida.html', {
        'sucursal': sucursal,
        'productos_recientes': productos_recientes,
    })


@login_required
def venta_rapida(request):
    """Vista para descuento rápido de productos (ventas múltiples)"""
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        messages.warning(request, '⚠️ Debes seleccionar una sucursal para realizar ventas')
        return redirect('sucursales:seleccionar')
    
    if request.method == 'POST':
        import json
        
        try:
            carrito_json = request.POST.get('carrito', '[]')
            carrito = json.loads(carrito_json)
            
            if not carrito or len(carrito) == 0:
                messages.error(request, '❌ El carrito está vacío')
                return redirect('inventario:venta_rapida')
            
            total_venta = 0
            productos_vendidos = []
            
            # Procesar cada producto del carrito
            with transaction.atomic():
                    for item in carrito:
                        codigo = item['codigo']
                        cantidad = int(item['cantidad'])
                        precio = float(item['precio'])
                        subtotal = float(item['subtotal'])
                        precio_minimo = float(item.get('precioMinimo', 0))  # ✅ NUEVO
                        
                        # Buscar inventario
                        inventario = InventarioSucursal.objects.select_related('producto').filter(
                            Q(producto__codigo=codigo),
                            sucursal=sucursal,
                            producto__activo=True
                        ).first()
                        
                        if not inventario:
                            raise ValueError(f'Producto {codigo} no encontrado')
                        
                        # ✅ VALIDAR PRECIO MÍNIMO EN BACKEND
                        if inventario.producto.precio_venta_minimo > 0 and precio < float(inventario.producto.precio_venta_minimo):
                            raise ValueError(
                                f'NO se puede vender {inventario.producto.nombre} por ${precio:.2f}. '
                                f'Precio mínimo: ${inventario.producto.precio_venta_minimo:.2f}'
                            )
                        
                        # Verificar stock
                        if inventario.cantidad < cantidad:
                            raise ValueError(
                                f'Stock insuficiente para {inventario.producto.nombre}. '
                                f'Disponible: {inventario.cantidad}'
                            )
                    
                    # Descontar stock
                    inventario.cantidad -= cantidad
                    inventario.save()
                    
                    # Registrar movimiento
                    MovimientoInventario.objects.create(
                        producto=inventario.producto,
                        sucursal=sucursal,
                        tipo='SALIDA',
                        cantidad=cantidad,
                        motivo='VENTA',
                        usuario=request.user,
                        observaciones=f'Venta: {cantidad} x ${precio:.2f} = ${subtotal:.2f} - {sucursal.nombre}'
                    )
                    
                    productos_vendidos.append(f'{inventario.producto.nombre} ({cantidad})')
                    total_venta += subtotal
                
                    # Registrar actividad
                    registrar_actividad(
                        request.user,
                        tipo='DESCONTAR',
                        descripcion=f'Venta múltiple: {len(carrito)} productos por ${total_venta:.2f}',
                        request=request
                    )
                    
                    messages.success(
                        request,
                        f'✅ Venta registrada exitosamente: {len(carrito)} productos por ${total_venta:.2f}'
                    )
                    return redirect('inventario:venta_rapida')
                
        except ValueError as e:
            messages.error(request, f'❌ {str(e)}')
            return redirect('inventario:venta_rapida')
        except Exception as e:
            messages.error(request, f'❌ Error al procesar venta: {str(e)}')
            return redirect('inventario:venta_rapida')
    
    # GET
    productos_recientes = InventarioSucursal.objects.filter(
        sucursal=sucursal,
        producto__activo=True,
        cantidad__gt=0
    ).select_related('producto', 'producto__categoria').order_by('-producto__id')[:20]
    
    return render(request, 'inventario/venta_rapida.html', {
        'sucursal': sucursal,
        'productos_recientes': productos_recientes,
    })

# ===============================
# AGREGAR PRODUCTO EXISTENTE A MI INVENTARIO
# ===============================
@login_required
def agregar_producto_existente(request):
    """Permite agregar un producto del catálogo global a la sucursal actual"""
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    # SUPER_ADMIN sin sucursal debe seleccionar una
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        messages.warning(request, 'Por favor selecciona una sucursal para agregar productos')
        return redirect('sucursales:seleccionar')
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad_inicial = int(request.POST.get('cantidad_inicial', 0))
        cantidad_minima = int(request.POST.get('cantidad_minima', 5))
        ubicacion = request.POST.get('ubicacion', '')
        
        try:
            producto = get_object_or_404(Producto, id=producto_id)
            
            # Verificar si ya existe en esta sucursal
            if InventarioSucursal.objects.filter(producto=producto, sucursal=sucursal).exists():
                messages.error(request, f'❌ El producto {producto.nombre} ya existe en tu inventario')
                return redirect('inventario:agregar_producto_existente')
            
            # Crear inventario en la sucursal
            InventarioSucursal.objects.create(
                producto=producto,
                sucursal=sucursal,
                cantidad=cantidad_inicial,
                cantidad_minima=cantidad_minima,
                ubicacion=ubicacion
            )
            
            # Si hay cantidad inicial, registrar movimiento
            if cantidad_inicial > 0:
                MovimientoInventario.objects.create(
                    producto=producto,
                    sucursal=sucursal,
                    tipo='ENTRADA',
                    cantidad=cantidad_inicial,
                    motivo='COMPRA',
                    usuario=request.user,
                    observaciones=f'Producto agregado a inventario de {sucursal.nombre}'
                )
            
            registrar_actividad(
                request.user,
                tipo='INVENTARIO',
                descripcion=f'Agregó producto {producto.nombre} a {sucursal.nombre}',
                request=request
            )
            
            messages.success(request, f'✅ Producto {producto.nombre} agregado exitosamente')
            return redirect('inventario:listar_productos')
            
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('inventario:agregar_producto_existente')
    
    # GET: Mostrar productos que NO están en esta sucursal
    productos_en_sucursal = InventarioSucursal.objects.filter(
        sucursal=sucursal
    ).values_list('producto_id', flat=True)
    
    productos_disponibles = Producto.objects.filter(
        activo=True
    ).exclude(
        id__in=productos_en_sucursal
    ).select_related('categoria', 'proveedor').order_by('nombre')
    
    context = {
        'sucursal': sucursal,
        'productos_disponibles': productos_disponibles,
    }
    return render(request, 'inventario/agregar_producto_existente.html', context)


@login_required
def buscar_productos_globales_ajax(request):
    """AJAX: Buscar productos del catálogo global"""
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, redirect):
        return JsonResponse({'productos': []})
    
    busqueda = request.GET.get('q', '').strip()
    
    if len(busqueda) < 2:
        return JsonResponse({'productos': []})
    
    # Productos que NO están en esta sucursal
    productos_en_sucursal = InventarioSucursal.objects.filter(
        sucursal=sucursal
    ).values_list('producto_id', flat=True)
    
    productos = Producto.objects.filter(
        Q(nombre__icontains=busqueda) | 
        Q(codigo__icontains=busqueda) |
        Q(codigo_barras__icontains=busqueda),
        activo=True
    ).exclude(
        id__in=productos_en_sucursal
    ).select_related('categoria', 'proveedor')[:10]
    
    resultados = [{
        'id': p.id,
        'codigo': p.codigo,
        'nombre': p.nombre,
        'categoria': p.categoria.nombre,
        'proveedor': p.proveedor.nombre if p.proveedor else 'Sin proveedor',
        'unidad_medida': p.get_unidad_medida_display(),
    } for p in productos]
    
    return JsonResponse({'productos': resultados})


# ===============================
# AJUSTES DE INVENTARIO (MERMA, DEVOLUCIONES, ETC)
# ===============================
@login_required
def ajustar_inventario(request, producto_id):
    """Ajustar inventario por merma, devolución, error, etc."""
    sucursal = obtener_sucursal_usuario(request)
    if isinstance(sucursal, HttpResponseRedirect):
        return sucursal
    
    if request.user.rol == 'SUPER_ADMIN' and sucursal is None:
        messages.warning(request, 'Por favor selecciona una sucursal')
        return redirect('sucursales:seleccionar')
    
    try:
        inventario = InventarioSucursal.objects.get(
            producto_id=producto_id,
            sucursal=sucursal
        )
    except InventarioSucursal.DoesNotExist:
        messages.error(request, 'Este producto no existe en tu sucursal')
        return redirect('inventario:listar_productos')
    
    if request.method == 'POST':
        try:
            tipo_ajuste = request.POST.get('tipo_ajuste')  # 'ENTRADA' o 'SALIDA'
            motivo = request.POST.get('motivo')
            cantidad = int(request.POST.get('cantidad', 0))
            observaciones = request.POST.get('observaciones', '')
            
            if cantidad <= 0:
                messages.error(request, 'La cantidad debe ser mayor a cero')
                return redirect('inventario:ajustar_inventario', producto_id)
            
            cantidad_anterior = inventario.cantidad
            
            # Aplicar ajuste
            if tipo_ajuste == 'ENTRADA':
                inventario.cantidad += cantidad
            elif tipo_ajuste == 'SALIDA':
                if cantidad > inventario.cantidad:
                    messages.error(request, f'No puedes descontar {cantidad}. Stock actual: {inventario.cantidad}')
                    return redirect('inventario:ajustar_inventario', producto_id)
                inventario.cantidad -= cantidad
            else:
                messages.error(request, 'Tipo de ajuste inválido')
                return redirect('inventario:ajustar_inventario', producto_id)
            
            inventario.save()
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                producto=inventario.producto,
                sucursal=sucursal,
                tipo=tipo_ajuste,
                cantidad=cantidad,
                motivo=motivo,
                usuario=request.user,
                observaciones=f'{observaciones} | Stock anterior: {cantidad_anterior} → Nuevo: {inventario.cantidad}'
            )
            
            registrar_actividad(
                request.user,
                tipo='AJUSTE',
                descripcion=f'Ajustó inventario de {inventario.producto.nombre}: {tipo_ajuste} de {cantidad}',
                request=request
            )
            
            # Mensaje específico según motivo
            motivo_display = dict(MovimientoInventario.MOTIVOS).get(motivo, motivo)
            messages.success(
                request,
                f'✅ Ajuste registrado: {motivo_display} - {cantidad} unidades ({tipo_ajuste.lower()})'
            )
            return redirect('inventario:detalle_producto', producto_id)
            
        except ValueError:
            messages.error(request, 'Cantidad inválida')
            return redirect('inventario:ajustar_inventario', producto_id)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('inventario:ajustar_inventario', producto_id)
    
    # GET
    return render(request, 'inventario/ajustar_inventario.html', {
        'producto': inventario.producto,
        'inventario': inventario,
        'sucursal': sucursal,
        'motivos': MovimientoInventario.MOTIVOS,
    })