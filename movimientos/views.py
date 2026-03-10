from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.utils import timezone

# Importar los modelos correctos desde la app inventario
from inventario.models import MovimientoInventario, AlertaInventario
from facturas.models import Factura
@login_required
def listar_movimientos_view(request):
    """Lista todos los movimientos"""
    dias = int(request.GET.get('dias', 7))
    fecha_desde = timezone.now() - timedelta(days=dias)
    
    movimientos = MovimientoInventario.objects.filter(
        fecha__gte=fecha_desde
    ).select_related('producto', 'usuario', 'sucursal').order_by('-fecha')
    
    context = {
        'movimientos': movimientos,
        'dias': dias,
    }
    return render(request, 'movimientos/listar.html', context)


@login_required
def listar_alertas_view(request):
    """Lista todas las alertas"""
    alertas = AlertaInventario.objects.filter(
        resuelta=False
    ).select_related('producto').order_by('-fecha_generada')
    
    context = {
        'alertas': alertas,
    }
    return render(request, 'movimientos/alertas.html', context)


@login_required
def panel_inventario(request):
    """Panel general de inventario y alertas"""
    dias = int(request.GET.get('dias', 7))
    fecha_inicio = timezone.now() - timedelta(days=dias)

    # Movimientos
    if request.user.rol in ['ADMIN', 'SUPER_ADMIN']:
        movimientos = MovimientoInventario.objects.filter(
            fecha__gte=fecha_inicio
        ).select_related('producto', 'usuario', 'sucursal').order_by('-fecha')
        
        alertas = AlertaInventario.objects.all().order_by('-fecha_generada')
    else:
        sucursal_id = request.session.get('sucursal_actual')
        movimientos = MovimientoInventario.objects.filter(
            fecha__gte=fecha_inicio,
            sucursal_id=sucursal_id
        ).select_related('producto', 'usuario').order_by('-fecha')
        
        alertas = AlertaInventario.objects.filter(
            producto__inventariosucursal__sucursal_id=sucursal_id
        ).order_by('-fecha_generada')

    return render(request, 'inventario/panel_inventario.html', {
        'movimientos': movimientos,
        'alertas': alertas,
        'dias': dias
    })

@login_required
def detalle_factura(request, id):
    factura = Factura.objects.get(id=id)
    detalles = factura.detalles.all()  # <- relacionado con el related_name
    return render(request, 'facturas/ver_factura.html', {
        'factura': factura,
        'detalles': detalles,
    })
