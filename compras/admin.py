from django.contrib import admin
from .models import SugerenciaCompra, ConfiguracionCompras


@admin.register(SugerenciaCompra)
class SugerenciaCompraAdmin(admin.ModelAdmin):
    list_display = [
        'producto', 'urgencia', 'cantidad_sugerida', 
        'stock_actual', 'dias_stock_restante', 'prediccion_proximos_30_dias',
        'tendencia', 'confianza_ia', 'fecha_generacion'
    ]
    list_filter = ['urgencia', 'tendencia', 'sucursal']
    search_fields = ['producto__nombre', 'producto__codigo']
    readonly_fields = ['fecha_generacion', 'generado_por', 'inversion_estimada']


@admin.register(ConfiguracionCompras)
class ConfiguracionComprasAdmin(admin.ModelAdmin):
    list_display = [
        'dias_cobertura_default', 'stock_seguridad_porcentaje',
        'habilitar_ia', 'ultima_actualizacion'
    ]