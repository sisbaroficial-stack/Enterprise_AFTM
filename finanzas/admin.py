"""
PANEL DE ADMINISTRACIÓN DE FINANZAS
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CategoriaGasto, Gasto, GastoRecurrente,
    Empleado, Nomina, Asistencia, Vacacion,
    Presupuesto, AnalisisFinanciero
)


@admin.register(CategoriaGasto)
class CategoriaGastoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'color_badge', 'activa', 'orden']
    list_filter = ['tipo', 'activa']
    search_fields = ['nombre']
    ordering = ['orden', 'nombre']
    
    def color_badge(self, obj):
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            obj.color, obj.get_tipo_display()
        )
    color_badge.short_description = 'Tipo'


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'concepto', 'monto', 'categoria', 'sucursal', 'estado_badge', 'registrado_por']
    list_filter = ['estado', 'categoria', 'sucursal', 'fecha']
    search_fields = ['concepto', 'notas']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha_registro', 'ultima_modificacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('fecha', 'sucursal', 'categoria', 'concepto', 'monto')
        }),
        ('Detalles', {
            'fields': ('metodo_pago', 'proveedor', 'es_recurrente', 'numero_factura', 'factura_adjunta', 'notas')
        }),
        ('Estado', {
            'fields': ('estado', 'aprobado_por', 'fecha_aprobacion', 'motivo_rechazo')
        }),
        ('Auditoría', {
            'fields': ('registrado_por', 'fecha_registro', 'ultima_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def estado_badge(self, obj):
        colores = {
            'PENDIENTE': 'warning',
            'APROBADO': 'success',
            'RECHAZADO': 'danger',
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colores.get(obj.estado, 'secondary'), obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(GastoRecurrente)
class GastoRecurrenteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'monto_base', 'dia_pago', 'sucursal', 'activo', 'auto_crear']
    list_filter = ['activo', 'auto_crear', 'sucursal']
    search_fields = ['nombre']


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'nombre_completo', 'cargo', 'sucursal', 'estado', 'salario_base']
    list_filter = ['estado', 'sucursal', 'tipo_contrato']
    search_fields = ['nombres', 'apellidos', 'numero_documento']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('tipo_documento', 'numero_documento', 'nombres', 'apellidos', 
                      'fecha_nacimiento', 'telefono', 'email', 'direccion', 'ciudad')
        }),
        ('Información Laboral', {
            'fields': ('cargo', 'sucursal', 'tipo_contrato', 'fecha_ingreso', 'fecha_retiro', 'estado')
        }),
        ('Información Salarial', {
            'fields': ('salario_base', 'auxilio_transporte')
        }),
        ('Relación con Sistema', {
            'fields': ('usuario',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Nomina)
class NominaAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'mes', 'anio', 'neto_pagar', 'pagado', 'fecha_pago']
    list_filter = ['pagado', 'mes', 'anio']
    search_fields = ['empleado__nombres', 'empleado__apellidos']
    readonly_fields = ['total_devengado', 'total_deducciones', 'neto_pagar', 
                       'total_aportes_empresa', 'costo_total_empresa']


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'fecha', 'hora', 'tipo']
    list_filter = ['tipo', 'fecha']
    date_hierarchy = 'fecha'


@admin.register(Vacacion)
class VacacionAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'fecha_inicio', 'fecha_fin', 'dias_totales', 'estado']
    list_filter = ['estado', 'fecha_inicio']


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ['categoria', 'sucursal', 'mes', 'anio', 'monto_presupuestado', 'porcentaje_usado']
    list_filter = ['mes', 'anio', 'sucursal']
    
    def porcentaje_usado(self, obj):
        return f"{obj.porcentaje_usado:.1f}%"
    porcentaje_usado.short_description = '% Usado'


