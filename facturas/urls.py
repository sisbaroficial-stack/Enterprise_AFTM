from django.urls import path
from . import views

app_name = 'Facturas'

urlpatterns = [
    # =============== FACTURAS ===============
    path('', views.lista_facturas, name='lista_facturas'),
    path('<int:factura_id>/', views.ver_factura_completa, name='ver_factura_completa'),
    path('<int:factura_id>/imprimir/', views.imprimir_factura, name='imprimir_factura'),
    path('<int:factura_id>/anular/', views.anular_factura, name='anular_factura'),
    
    # =============== CLIENTES ===============
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/buscar-ajax/', views.buscar_cliente_ajax, name='buscar_cliente_ajax'),
]