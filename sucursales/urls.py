from django.urls import path
from . import views

app_name = 'sucursales'

urlpatterns = [
    # Selección de sucursal
    path('seleccionar/', views.seleccionar_sucursal, name='seleccionar'),
    path('establecer/<int:sucursal_id>/', views.establecer_sucursal, name='establecer'),
    path('establecer-todas/', views.establecer_todas_sucursales, name='establecer_todas'),  # NUEVA LÍNEA

    # Inventario por sucursal
    path('inventario/', views.inventario_sucursal, name='inventario'),
    
    # Transferencias
    path('transferencias/', views.lista_transferencias, name='lista_transferencias'),
    path('transferencias/crear/', views.crear_transferencia, name='crear_transferencia'),
    path('transferencias/recibir/<int:transferencia_id>/', views.recibir_transferencia, name='recibir_transferencia'),
    
    # Gestión de sucursales (Admin)
    path('gestionar/', views.gestionar_sucursales, name='gestionar'),
    path('crear/', views.crear_sucursal_view, name='crear'),
    path('editar/<int:sucursal_id>/', views.editar_sucursal_view, name='editar'),
    path('', views.gestionar_sucursales, name='listar_sucursales'),


]