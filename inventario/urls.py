from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # =============== PRODUCTOS ===============
    path('', views.lista_productos, name='listar_productos'),
    path('crear/', views.crear_producto, name='crear_producto'),
    path('editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('ver/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    
    # Stock
    path('agregar-existente/', views.agregar_producto_existente, name='agregar_producto_existente'),
    path('buscar-productos-globales/', views.buscar_productos_globales_ajax, name='buscar_productos_globales_ajax'),
    path('descontar/<int:producto_id>/', views.descontar_producto, name='descontar_producto'),
    path('agregar/<int:producto_id>/', views.agregar_stock, name='agregar_stock'),
    path('ajustar/<int:producto_id>/', views.ajustar_inventario, name='ajustar_inventario'),
    
    # =============== VENTAS ===============
    path('venta-rapida/', views.venta_rapida, name='venta_rapida'),
    
    # =============== FACTURACIÓN ===============

    
    # =============== OTROS ===============
    path('buscar-ajax/', views.buscar_producto_ajax, name='buscar_producto_ajax'),
    path('movimientos/', views.listar_movimientos, name='listar_movimientos'),
    path('panel/', views.panel_inventario, name='panel_inventario'),
    

]
