from django.contrib import admin
from .models import Notificacion

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'titulo', 'sucursal', 'usuario_accion', 'leida', 'fecha_creacion']
    list_filter = ['tipo', 'leida', 'sucursal']
    search_fields = ['titulo', 'mensaje']
    date_hierarchy = 'fecha_creacion'