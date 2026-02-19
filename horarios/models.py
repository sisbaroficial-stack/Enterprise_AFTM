from django.db import models
from django.conf import settings

DIAS_SEMANA = [
    (0, 'Lunes'),
    (1, 'Martes'),
    (2, 'Miércoles'),
    (3, 'Jueves'),
    (4, 'Viernes'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]


class PlantillaHorario(models.Model):
    """
    Define un horario reutilizable que el Super Admin puede crear
    y luego asignar a cualquier usuario con cuenta.
    Ej: 'Turno Mañana', 'Turno Noche', 'Medio Tiempo'
    """
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Turno')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    color = models.CharField(
        max_length=7,
        default='#4e73df',
        verbose_name='Color identificador',
        help_text='Color en formato HEX, ej: #4e73df'
    )
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='plantillas_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plantilla de Horario'
        verbose_name_plural = 'Plantillas de Horario'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def dias_laborales(self):
        return self.dias.filter(es_descanso=False).count()

    def dias_descanso(self):
        return self.dias.filter(es_descanso=True).count()


class DiaHorario(models.Model):
    """
    Representa un día específico dentro de una PlantillaHorario.
    Puede ser día laboral (con hora entrada/salida) o día de descanso.
    """
    plantilla = models.ForeignKey(
        PlantillaHorario,
        on_delete=models.CASCADE,
        related_name='dias'
    )
    dia_semana = models.IntegerField(choices=DIAS_SEMANA, verbose_name='Día')
    es_descanso = models.BooleanField(default=False, verbose_name='Día de Descanso')
    hora_entrada = models.TimeField(null=True, blank=True, verbose_name='Hora de Entrada')
    hora_salida = models.TimeField(null=True, blank=True, verbose_name='Hora de Salida')

    class Meta:
        verbose_name = 'Día de Horario'
        verbose_name_plural = 'Días de Horario'
        ordering = ['dia_semana']
        unique_together = ['plantilla', 'dia_semana']

    def __str__(self):
        if self.es_descanso:
            return f"{self.get_dia_semana_display()} - 😴 Descanso"
        return f"{self.get_dia_semana_display()} {self.hora_entrada} - {self.hora_salida}"

    def duracion_horas(self):
        if self.es_descanso or not self.hora_entrada or not self.hora_salida:
            return 0
        from datetime import datetime, date
        entrada = datetime.combine(date.today(), self.hora_entrada)
        salida = datetime.combine(date.today(), self.hora_salida)
        diff = salida - entrada
        return round(diff.seconds / 3600, 1)


class AsignacionHorario(models.Model):
    """
    Relaciona un Usuario (con cuenta) a una PlantillaHorario.
    Un usuario solo puede tener UNA asignación activa a la vez.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='horarios_asignados'
    )
    plantilla = models.ForeignKey(
        PlantillaHorario,
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de Fin')
    activo = models.BooleanField(default=True, verbose_name='Asignación Activa')
    notas = models.TextField(blank=True, null=True, verbose_name='Notas adicionales')
    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='horarios_asignados_por_mi'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Asignación de Horario'
        verbose_name_plural = 'Asignaciones de Horario'
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"{self.usuario.get_full_name()} → {self.plantilla.nombre}"