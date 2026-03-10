from django.contrib import admin
from .models import Cliente, Factura, DetalleFactura


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'nombre_completo', 'telefono', 'ciudad', 'activo']
    search_fields = ['numero_documento', 'nombre_completo', 'email']
    list_filter = ['tipo_documento', 'activo', 'ciudad']


class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 0


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['numero_factura', 'cliente', 'sucursal', 'total', 'fecha', 'anulada']
    search_fields = ['numero_factura', 'cliente__nombre_completo']
    list_filter = ['sucursal', 'metodo_pago', 'anulada', 'fecha']
    inlines = [DetalleFacturaInline]
    readonly_fields = ['numero_factura', 'fecha']