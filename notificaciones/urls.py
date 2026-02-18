from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # API
    path('api/recientes/', views.api_notificaciones_recientes, name='api_recientes'),
    
    # Acciones
    path('<int:notif_id>/marcar-leida/', views.marcar_leida, name='marcar_leida'),
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    
    # Vistas
    path('todas/', views.todas_notificaciones, name='todas'),
]