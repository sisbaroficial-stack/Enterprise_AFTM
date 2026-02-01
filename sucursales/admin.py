from django.contrib import admin
from .models import Sucursal

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'activa', 'es_principal', 'encargado']
    list_filter = ['tipo', 'activa', 'es_principal']
    search_fields = ['nombre', 'codigo']
    list_editable = ['activa']