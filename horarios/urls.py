from django.urls import path
from . import views

app_name = 'horarios'

urlpatterns = [
    # Plantillas (Super Admin)
    path('plantillas/', views.lista_plantillas, name='lista_plantillas'),
    path('plantillas/crear/', views.crear_plantilla, name='crear_plantilla'),
    path('plantillas/editar/<int:plantilla_id>/', views.editar_plantilla, name='editar_plantilla'),
    path('plantillas/eliminar/<int:plantilla_id>/', views.eliminar_plantilla, name='eliminar_plantilla'),

    # Asignaciones (Admin / Super Admin)
    path('asignaciones/', views.lista_asignaciones, name='lista_asignaciones'),
    path('asignaciones/asignar/', views.asignar_horario, name='asignar_horario'),
    path('asignaciones/asignar/<int:usuario_id>/', views.asignar_horario, name='asignar_horario_usuario'),
    path('asignaciones/desactivar/<int:asignacion_id>/', views.desactivar_asignacion, name='desactivar_asignacion'),

    # Empleado
    path('mi-horario/', views.mi_horario, name='mi_horario'),
]