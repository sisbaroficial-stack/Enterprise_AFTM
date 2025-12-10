from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from inventario.models import Producto
from categorias.models import Categoria
from movimientos.models import Movimiento, AlertaInventario
from usuarios.models import HistorialActividad, Usuario


@login_required
def home_view(request):
    """
    Dashboard principal optimizado con estadísticas en tiempo real
    """

    # Estadísticas de productos (una sola consulta)
    stats_productos = Producto.objects.filter(activo=True).aggregate(
        total=Count('id'),
        disponibles=Count('id', filter=Q(estado='DISPONIBLE')),
        por_agotar=Count('id', filter=Q(estado='POR_AGOTAR')),
        agotados=Count('id', filter=Q(estado='AGOTADO')),
        valor_total=Sum('precio_compra')
    )

    # Productos por categoría (limitado a top 5)
    productos_por_categoria = Categoria.objects.filter(activa=True).annotate(
        total=Count('productos', filter=Q(productos__activo=True))
    ).order_by('-total')[:5]

    # Productos con stock bajo (top 5)
    productos_stock_bajo = Producto.objects.filter(
        activo=True,
        cantidad__lte=5
    ).order_by('cantidad')[:5]

    # Últimos movimientos (últimos 7 días, top 10)
    hace_7_dias = timezone.now() - timedelta(days=7)
    ultimos_movimientos = Movimiento.objects.filter(
        fecha__gte=hace_7_dias
    ).select_related('producto', 'usuario').order_by('-fecha')[:10]

    # Actividad reciente del usuario (top 5)
    actividad_reciente = HistorialActividad.objects.filter(
        usuario=request.user
    ).order_by('-fecha')[:5]

    # Alertas pendientes (top 5)
    alertas_pendientes = AlertaInventario.objects.filter(
        resuelta=False
    ).select_related('producto').order_by('-fecha_generada')[:5]

    # Movimientos de hoy
    hoy = timezone.now().date()
    movimientos_hoy = Movimiento.objects.filter(
        fecha__date=hoy
    ).count()

    # Productos más movidos últimos 30 días (top 5)
    hace_30_dias = timezone.now() - timedelta(days=30)
    productos_mas_movidos = Producto.objects.filter(
        activo=True,
        movimientos__fecha__gte=hace_30_dias
    ).annotate(
        total_movimientos=Count('movimientos')
    ).order_by('-total_movimientos')[:5]

    # Datos para gráfica de categorías
    categorias_labels = [f"{cat.icono} {cat.nombre}" for cat in productos_por_categoria]
    categorias_data = [cat.total for cat in productos_por_categoria]
    categorias_colors = [cat.color for cat in productos_por_categoria]

    # Estadísticas de usuarios (solo para admins)
    stats_usuarios = None
    if request.user.puede_aprobar():
        usuarios_agg = Usuario.objects.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(is_active=True)),
            pendientes=Count('id', filter=Q(aprobado=False))
        )
        stats_usuarios = usuarios_agg

    context = {
        # Estadísticas principales
        'total_productos': stats_productos['total'],
        'productos_disponibles': stats_productos['disponibles'],
        'productos_por_agotar': stats_productos['por_agotar'],
        'productos_agotados': stats_productos['agotados'],
        'valor_total': stats_productos['valor_total'] or 0,
        'movimientos_hoy': movimientos_hoy,

        # Listas
        'productos_por_categoria': productos_por_categoria,
        'productos_stock_bajo': productos_stock_bajo,
        'ultimos_movimientos': ultimos_movimientos,
        'actividad_reciente': actividad_reciente,
        'alertas_pendientes': alertas_pendientes,
        'productos_mas_movidos': productos_mas_movidos,

        # Datos para gráficas
        'categorias_labels': categorias_labels,
        'categorias_data': categorias_data,
        'categorias_colors': categorias_colors,

        # Estadísticas de usuarios
        'stats_usuarios': stats_usuarios,
    }

    return render(request, 'dashboard/home.html', context)
