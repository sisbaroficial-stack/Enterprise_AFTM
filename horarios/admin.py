from django.contrib import admin
from .models import PlantillaHorario, DiaHorario, AsignacionHorario

class DiaHorarioInline(admin.TabularInline):
    model = DiaHorario
    extra = 7
    max_num = 7

@admin.register(PlantillaHorario)
class PlantillaHorarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'dias_laborales', 'dias_descanso', 'fecha_creacion']
    inlines = [DiaHorarioInline]

@admin.register(AsignacionHorario)
class AsignacionHorarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'plantilla', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter = ['activo', 'plantilla']