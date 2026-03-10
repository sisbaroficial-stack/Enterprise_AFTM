
```
SISBAR1.1_AFTM-SAS
├─ build.sh
├─ categorias
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ dashboard
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ facturas
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ inventario
│  ├─ admin.py
│  ├─ apps.py
│  ├─ forms.py
│  ├─ management
│  │  ├─ commands
│  │  │  ├─ stress_test_sisbar.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_alter_transferenciasucursal_estado_alertainventario.py
│  │  ├─ 0003_alter_movimientoinventario_options_and_more.py
│  │  ├─ 0004_producto_margen_ganancia_producto_precio_venta_and_more.py
│  │  ├─ 0005_factura_detallefactura_movimientoinventario_factura.py
│  │  ├─ 0006_cliente_factura_anulada_factura_cambio_and_more.py
│  │  ├─ 0007_remove_factura_cliente_remove_detallefactura_factura_and_more.py
│  │  ├─ 0008_movimientoinventario_factura.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ manage.py
├─ movimientos
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_alter_movimiento_producto.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ productos
│  ├─ Acer_Wallpaper_01_5000x2814_-_copia.jpg
│  ├─ Acer_Wallpaper_02_5000x2813_-_copia.jpg
│  ├─ Acer_Wallpaper_03_5000x2814_-_copia.jpg
│  ├─ Planet9_Wallpaper_5000x2813_-_copia.jpg
│  └─ WhatsApp_Image_2026-01-22_at_20.42.52.jpeg
├─ proveedores
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ README.md
├─ render.yaml
├─ reportes
│  ├─ admin.py
│  ├─ apps.py
│  ├─ home.html
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ requirements.txt
├─ sisbar_config
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ views.py
│  ├─ wsgi.py
│  └─ __init__.py
├─ sucursales
│  ├─ admin.py
│  ├─ apps.py
│  ├─ context_processors.py
│  ├─ middleware.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_sucursal_aplica_impuesto_consumo_and_more.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ templates
│  ├─ base.html
│  ├─ categorias
│  │  ├─ crear.html
│  │  ├─ crear_subcategoria.html
│  │  ├─ editar.html
│  │  ├─ eliminar.html
│  │  └─ listar.html
│  ├─ dashboard
│  │  └─ home.html
│  ├─ facturas
│  │  ├─ anular.html
│  │  ├─ clientes
│  │  │  ├─ crear.html
│  │  │  ├─ editar.html
│  │  │  └─ lista.html
│  │  ├─ imprimir.html
│  │  ├─ lista.html
│  │  └─ ver_factura.html
│  ├─ index.html
│  ├─ inventario
│  │  ├─ agregar_producto_existente.html
│  │  ├─ agregar_stock.html
│  │  ├─ ajustar_inventario.html
│  │  ├─ crear_producto.html
│  │  ├─ descontar_producto.html
│  │  ├─ detalle_factura.html
│  │  ├─ eliminar_producto.html
│  │  ├─ form_producto.html
│  │  ├─ listar_productos.html
│  │  ├─ venta_rapida.html
│  │  └─ ver_producto.html
│  ├─ movimientos
│  │  ├─ alertas.html
│  │  ├─ listar.html
│  │  └─ panel_inventario.html
│  ├─ proveedores
│  │  ├─ crear.html
│  │  ├─ editar.html
│  │  ├─ eliminar.html
│  │  ├─ listar.html
│  │  └─ ver.html
│  ├─ reportes
│  │  ├─ home.html
│  │  ├─ reporte_abc.html
│  │  ├─ reporte_rotacion.html
│  │  └─ sin_movimiento.html
│  ├─ sucursales
│  │  ├─ crear.html
│  │  ├─ crear_transferencia.html
│  │  ├─ editar.html
│  │  ├─ gestionar.html
│  │  ├─ inventario.html
│  │  ├─ lista_transferencias.html
│  │  └─ seleccionar.html
│  └─ usuarios
│     ├─ aprobar_usuario.html
│     ├─ asignar_sucursal.html
│     ├─ cambiar_password.html
│     ├─ crear_grupo.html
│     ├─ detalle_usuario.html
│     ├─ editar_grupo.html
│     ├─ editar_usuario_completo.html
│     ├─ eliminar_usuario.html
│     ├─ gestionar_grupos.html
│     ├─ gestionar_usuarios.html
│     ├─ login.html
│     ├─ panel_eliminados.html
│     ├─ perfil.html
│     ├─ registro.html
│     └─ resetear_password.html
└─ usuarios
   ├─ admin.py
   ├─ apps.py
   ├─ emails.py
   ├─ forms.py
   ├─ management
   │  ├─ commands
   │  │  ├─ crear_superadmin.py
   │  │  └─ __init__.py
   │  └─ __init__.py
   ├─ migrations
   │  ├─ 0001_initial.py
   │  ├─ 0002_usuario_notificado_aprobacion.py
   │  ├─ 0003_usuario_sucursal.py
   │  ├─ 0004_alter_usuario_rol.py
   │  └─ __init__.py
   ├─ models.py
   ├─ perfiles
   │  └─ Acer_Wallpaper_02_5000x2813_-_copia.jpg
   ├─ signals.py
   ├─ tests.py
   ├─ urls.py
   ├─ views.py
   └─ __init__.py

```