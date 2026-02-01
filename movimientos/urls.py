from django.urls import path
from . import views

app_name = 'movimientos'

urlpatterns = [
    path('', views.panel_inventario, name='panel_inventario'),  # Panel general
    path('listar/', views.listar_movimientos_view, name='listar_movimientos'),  # Lista de movimientos
    path('alertas/', views.listar_alertas_view, name='listar_alertas'),  # Lista de alertas
]
