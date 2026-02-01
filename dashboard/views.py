from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
import json

from inventario.models import Producto, InventarioSucursal, MovimientoInventario
from categorias.models import Categoria
from sucursales.models import Sucursal
from usuarios.models import HistorialActividad, Usuario


def obtener_sucursal_dashboard(request):
    """Helper para obtener la sucursal del usuario"""
    if request.user.rol == 'SUPER_ADMIN':
        sucursal_id = request.session.get('sucursal_actual')
        if sucursal_id:
            try:
                return Sucursal.objects.get(id=sucursal_id)
            except Sucursal.DoesNotExist:
                pass
        return None  # Modo global
    elif hasattr(request.user, 'sucursal') and request.user.sucursal:
        return request.user.sucursal
    return None


@login_required
def home_view(request):
    """Dashboard principal optimizado con estadísticas por sucursal"""
    
    # Obtener sucursal
    sucursal = obtener_sucursal_dashboard(request)
    
    # === FILTRAR DATOS POR SUCURSAL ===
    if request.user.rol == 'SUPER_ADMIN' and not sucursal:
        # Modo global: ver todo
        inventarios = InventarioSucursal.objects.select_related('producto', 'sucursal')
        movimientos_query = MovimientoInventario.objects.all()
        productos_query = Producto.objects.filter(activo=True)
    else:
        # Filtrar por sucursal específica
        if not sucursal:
            inventarios = InventarioSucursal.objects.none()
            movimientos_query = MovimientoInventario.objects.none()
            productos_query = Producto.objects.none()
        else:
            inventarios = InventarioSucursal.objects.filter(
                sucursal=sucursal
            ).select_related('producto', 'sucursal')
            movimientos_query = MovimientoInventario.objects.filter(sucursal=sucursal)
            productos_query = Producto.objects.filter(
                activo=True,
                inventarios__sucursal=sucursal
            ).distinct()
    
    # === ESTADÍSTICAS PRINCIPALES ===
    total_productos = inventarios.values('producto').distinct().count()
    
    # Calcular valor total del inventario
    valor_total = 0
    for inv in inventarios:
        if inv.producto.precio_compra:
            valor_total += inv.cantidad * inv.producto.precio_compra
    
    # Productos por estado
    productos_disponibles = inventarios.filter(
        cantidad__gt=F('cantidad_minima')
    ).values('producto').distinct().count()
    
    productos_por_agotar = inventarios.filter(
        cantidad__lte=F('cantidad_minima'),
        cantidad__gt=0
    ).values('producto').distinct().count()
    
    productos_agotados = inventarios.filter(
        cantidad=0
    ).values('producto').distinct().count()
    
    # === PRODUCTOS CON STOCK BAJO ===
    productos_stock_bajo = []
    inventarios_bajo = inventarios.filter(
        Q(cantidad__lte=F('cantidad_minima')) | Q(cantidad=0)
    ).select_related('producto').order_by('cantidad')[:6]
    
    for inv in inventarios_bajo:
        productos_stock_bajo.append({
            'id': inv.producto.id,
            'nombre': inv.producto.nombre,
            'codigo': inv.producto.codigo,
            'cantidad': inv.cantidad,
            'unidad_medida': inv.producto.unidad_medida,
            'get_estado_color': 'danger' if inv.cantidad == 0 else 'warning'
        })
    
    # === MOVIMIENTOS ===
    hoy = timezone.now().date()
    movimientos_hoy = movimientos_query.filter(fecha__date=hoy).count()
    
    hace_7_dias = timezone.now() - timedelta(days=7)
    ultimos_movimientos = movimientos_query.filter(
        fecha__gte=hace_7_dias
    ).select_related('producto', 'usuario', 'sucursal').order_by('-fecha')[:10]
    
    # Agregar métodos helper
    for mov in ultimos_movimientos:
        mov.get_tipo_icono = '↑' if mov.tipo == 'ENTRADA' else '↓'
    
    # === PRODUCTOS MÁS MOVIDOS (últimos 30 días) ===
    hace_30_dias = timezone.now() - timedelta(days=30)
    
    # Obtener IDs de productos con movimientos recientes en la sucursal
    if request.user.rol == 'SUPER_ADMIN' and not sucursal:
        # Global
        movimientos_recientes = MovimientoInventario.objects.filter(
            fecha__gte=hace_30_dias
        ).values('producto').annotate(
            total=Count('id')
        ).order_by('-total')[:5]
    else:
        # Por sucursal
        movimientos_recientes = MovimientoInventario.objects.filter(
            fecha__gte=hace_30_dias,
            sucursal=sucursal
        ).values('producto').annotate(
            total=Count('id')
        ).order_by('-total')[:5]
    
    # Obtener los productos completos
    productos_mas_movidos = []
    for mov in movimientos_recientes:
        try:
            producto = Producto.objects.get(id=mov['producto'])
            producto.total_movimientos = mov['total']
            productos_mas_movidos.append(producto)
        except Producto.DoesNotExist:
            pass
    
    # === PRODUCTOS POR CATEGORÍA ===
    if request.user.rol == 'SUPER_ADMIN' and not sucursal:
        productos_por_categoria = Categoria.objects.filter(
            activa=True
        ).annotate(
            total=Count('productos', filter=Q(productos__activo=True))
        ).order_by('-total')[:6]
    else:
        productos_ids = inventarios.values_list('producto_id', flat=True)
        productos_por_categoria = Categoria.objects.filter(
            activa=True,
            productos__id__in=productos_ids
        ).annotate(
            total=Count('productos', distinct=True)
        ).order_by('-total')[:6]
    
    categorias_labels = [f"{cat.icono} {cat.nombre}" if hasattr(cat, 'icono') and cat.icono else cat.nombre 
                         for cat in productos_por_categoria]
    categorias_data = [cat.total for cat in productos_por_categoria]
    categorias_colors = [
        cat.color if hasattr(cat, 'color') and cat.color else color 
        for cat, color in zip(productos_por_categoria, 
                             ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a'])
    ]
    
    # === ACTIVIDAD DEL USUARIO ===
    actividad_reciente = HistorialActividad.objects.filter(
        usuario=request.user
    ).order_by('-fecha')[:8]
    
    # === ALERTAS (simuladas desde stock bajo) ===
    alertas_pendientes = []
    for inv in inventarios_bajo[:5]:
        if inv.cantidad == 0:
            mensaje = f"Producto agotado - Sin stock disponible"
        elif inv.cantidad <= inv.cantidad_minima:
            mensaje = f"Stock bajo - Solo quedan {inv.cantidad} {inv.producto.unidad_medida}"
        else:
            continue
        
        alertas_pendientes.append({
            'producto': {
                'id': inv.producto.id,
                'nombre': inv.producto.nombre,
                'get_estado_color': 'danger' if inv.cantidad == 0 else 'warning'
            },
            'mensaje': mensaje
        })
    
    # === ESTADÍSTICAS DE USUARIOS (solo admins) ===
    stats_usuarios = None
    if request.user.puede_aprobar():
        stats_usuarios = {
            'total': Usuario.objects.count(),
            'activos': Usuario.objects.filter(is_active=True, aprobado=True).count(),
            'pendientes': Usuario.objects.filter(aprobado=False).count()
        }
    
    context = {
        'now': timezone.now(),
        'sucursal': sucursal,
        
        # Estadísticas principales
        'total_productos': total_productos,
        'productos_disponibles': productos_disponibles,
        'productos_por_agotar': productos_por_agotar,
        'productos_agotados': productos_agotados,
        'valor_total': valor_total,
        
        # Movimientos
        'movimientos_hoy': movimientos_hoy,
        'ultimos_movimientos': ultimos_movimientos,
        
        # Productos
        'productos_stock_bajo': productos_stock_bajo,
        'productos_mas_movidos': productos_mas_movidos,
        'productos_por_categoria': productos_por_categoria,
        
        # Actividad
        'actividad_reciente': actividad_reciente,
        
        # Gráficas (convertir a JSON)
        'categorias_labels': json.dumps(categorias_labels),
        'categorias_data': json.dumps(categorias_data),
        'categorias_colors': json.dumps(categorias_colors),
        
        # Alertas
        'alertas_pendientes': alertas_pendientes,
        
        # Usuarios
        'stats_usuarios': stats_usuarios,
    }
    
    return render(request, 'dashboard/home.html', context)
