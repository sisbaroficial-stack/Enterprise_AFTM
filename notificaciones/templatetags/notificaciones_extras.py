from django import template

register = template.Library()


@register.filter
def get_color_tipo(notificacion):
    """Retorna el color según el tipo de notificación"""
    colores = {
        'VENTA': 'success',
        'FACTURA_ANULADA': 'danger',
        'PRODUCTO_CREADO': 'primary',
        'PRODUCTO_EDITADO': 'info',
        'PRODUCTO_ELIMINADO': 'danger',
        'STOCK_AGREGADO': 'success',
        'STOCK_DESCONTADO': 'warning',
        'AJUSTE_INVENTARIO': 'info',
        'ALERTA_STOCK_BAJO': 'warning',
        'TRANSFERENCIA_CREADA': 'primary',
        'TRANSFERENCIA_ENVIADA': 'info',
        'TRANSFERENCIA_RECIBIDA': 'success',
        'GASTO_REGISTRADO': 'secondary',
        'GASTO_APROBADO': 'success',
        'GASTO_RECHAZADO': 'danger',
        'GASTO_PENDIENTE': 'warning',
        'NOMINA_GENERADA': 'success',
        'EMPLEADO_CREADO': 'primary',
        'EMPLEADO_EDITADO': 'info',
        'USUARIO_REGISTRADO': 'primary',
    }
    return colores.get(notificacion.tipo, 'secondary')


@register.filter
def get_icono_tipo(notificacion):
    """Retorna el icono de Bootstrap Icons según el tipo"""
    iconos = {
        'VENTA': 'cart-check',
        'FACTURA_ANULADA': 'x-circle',
        'PRODUCTO_CREADO': 'box-seam',
        'PRODUCTO_EDITADO': 'pencil',
        'PRODUCTO_ELIMINADO': 'trash',
        'STOCK_AGREGADO': 'arrow-up-circle',
        'STOCK_DESCONTADO': 'arrow-down-circle',
        'AJUSTE_INVENTARIO': 'sliders',
        'ALERTA_STOCK_BAJO': 'exclamation-triangle',
        'TRANSFERENCIA_CREADA': 'truck',
        'TRANSFERENCIA_ENVIADA': 'send',
        'TRANSFERENCIA_RECIBIDA': 'inbox',
        'GASTO_REGISTRADO': 'cash',
        'GASTO_APROBADO': 'check-circle',
        'GASTO_RECHAZADO': 'x-circle',
        'GASTO_PENDIENTE': 'clock',
        'NOMINA_GENERADA': 'cash-stack',
        'EMPLEADO_CREADO': 'person-plus',
        'EMPLEADO_EDITADO': 'person-check',
        'USUARIO_REGISTRADO': 'person-add',
    }
    return iconos.get(notificacion.tipo, 'bell')