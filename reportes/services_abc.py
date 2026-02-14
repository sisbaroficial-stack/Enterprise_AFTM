from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, F
from decimal import Decimal

from inventario.models import Producto, MovimientoInventario


class ServicioClasificacionABC:

    @staticmethod
    def recalcular_abc(dias=30):
        fecha_desde = timezone.now() - timedelta(days=dias)

        ventas_por_producto = MovimientoInventario.objects.filter(
            fecha__gte=fecha_desde,
            tipo='SALIDA',
            motivo='VENTA'
        ).values('producto').annotate(
            valor_total=Sum(F('cantidad') * F('producto__precio_compra'))
        ).order_by('-valor_total')

        total_ventas = sum(item['valor_total'] or 0 for item in ventas_por_producto)

        acumulado = Decimal('0')

        for item in ventas_por_producto:
            producto = Producto.objects.get(id=item['producto'])
            valor = item['valor_total'] or Decimal('0')

            porcentaje = (valor / total_ventas * 100) if total_ventas > 0 else 0
            acumulado += porcentaje

            if acumulado <= 80:
                clase = 'A'
            elif acumulado <= 95:
                clase = 'B'
            else:
                clase = 'C'

            # 🔥 Guardar en producto
            producto.clase_abc = clase
            producto.save(update_fields=['clase_abc'])
