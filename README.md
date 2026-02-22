
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
├─ compras
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_cacheprediccion.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ services.py
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
├─ dataset_ia_sisbar.json
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
├─ finanzas
│  ├─ admin.py
│  ├─ apps.py
│  ├─ forms.py
│  ├─ management
│  │  ├─ commands
│  │  │  ├─ cargar_categorias_gastos.py
│  │  │  ├─ generar_gastos_prueba.py
│  │  │  └─ __init__.py
│  │  └─ fsdfsf
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_registroasistencia_turno_horarioempleado.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ services
│  │  ├─ calculador_finanzas.py
│  │  ├─ exportador.py
│  │  ├─ ia_predictor.py
│  │  ├─ nomina_colombia.py
│  │  └─ __init__.py
│  ├─ signals.py
│  ├─ templatetags
│  │  └─ __init__.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ utils.py
│  ├─ views.py
│  ├─ views_avanzadas.py
│  └─ __init__.py
├─ horarios
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
│  │  │  ├─ test_ia_profundo.py
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
│  │  ├─ 0009_producto_clase_abc.py
│  │  ├─ 0010_alter_producto_clase_abc.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ limpiar_json.py
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
├─ notificaciones
│  ├─ admin.py
│  ├─ apps.py
│  ├─ management
│  │  ├─ commands
│  │  │  ├─ test_notificaciones.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ templatetags
│  │  ├─ notificaciones_extras.py
│  │  └─ __init__.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ productos
│  ├─ Acer_Wallpaper_01_5000x2814_-_copia.jpg
│  ├─ Acer_Wallpaper_01_5000x2814_-_copia_2lFYSk5.jpg
│  ├─ Acer_Wallpaper_02_5000x2813_-_copia.jpg
│  ├─ Acer_Wallpaper_03_5000x2814_-_copia.jpg
│  ├─ Planet9_Wallpaper_5000x2813_-_copia.jpg
│  └─ WhatsApp_Image_2026-01-22_at_20.42.52.jpeg
├─ proveedores
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_proveedor_cantidad_minima_pedido_and_more.py
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
│  ├─ services_abc.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ reporte_mega_test_saas.json
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
│  │  ├─ 0003_alter_sucursal_rango_hasta.py
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
│  ├─ compras
│  │  ├─ configuracion.html
│  │  ├─ detalle_sugerencia.html
│  │  ├─ partials
│  │  │  └─ card_sugerencia.html
│  │  └─ sugerencias.html
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
│  ├─ finanzas
│  │  ├─ analisis
│  │  │  └─ principal.html
│  │  ├─ dashboard.html
│  │  ├─ empleados
│  │  │  ├─ crear_completo.html
│  │  │  ├─ detalle_completo.html
│  │  │  ├─ detalle_empleado.html
│  │  │  ├─ editar.html
│  │  │  └─ lista_completa.html
│  │  ├─ gastos
│  │  │  ├─ detalle.html
│  │  │  ├─ lista.html
│  │  │  ├─ rechazar.html
│  │  │  └─ registrar.html
│  │  ├─ horarios
│  │  ├─ manual
│  │  │  └─ guia.html
│  │  └─ nomina
│  │     ├─ detalle_completa.html
│  │     ├─ generar_completa.html
│  │     └─ lista_completa.html
│  ├─ horarios
│  │  ├─ asignar_horario.html
│  │  ├─ confirmar_eliminar_plantilla.html
│  │  ├─ crear_plantilla.html
│  │  ├─ editar_plantilla.html
│  │  ├─ lista_asignaciones.html
│  │  ├─ lista_plantillas.html
│  │  └─ mi_horario.html
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
│  ├─ notificaciones
│  │  └─ todas.html
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

## Informe QA Backend (auditoria)

Fecha de auditoria: 2026-02-21

### Alcance ejecutado

- `python manage.py test usuarios.test_backend_qa -v 2`
- `python manage.py test -v 2`
- `python manage.py check`
- `python manage.py check --deploy`
- `python manage.py makemigrations --check --dry-run`

### Resultado general

- Se ejecuto una suite QA de smoke/integracion backend en `usuarios/test_backend_qa.py`.
- Se detectaron errores funcionales reales en rutas autenticadas.
- Se detectaron migraciones pendientes en `finanzas`.
- Se detectaron advertencias de seguridad para entorno productivo.

### Errores exactos encontrados y solucion propuesta

1. Error `NoReverseMatch` en clientes de facturas  
   Ubicacion: `facturas/views.py:267` (render de `facturas/clientes/lista.html`)  
   Error exacto: `Reverse for 'crear_cliente' not found`  
   Causa probable: en plantilla se usa `{% url 'crear_cliente' %}` sin namespace.  
   Solucion: cambiar a `{% url 'facturas:crear_cliente' %}` en `templates/facturas/clientes/lista.html`.

2. Error `TemplateDoesNotExist` en comparativas de finanzas  
   Ubicacion: `finanzas/views.py:658`  
   Error exacto: `finanzas/analisis/comparativas.html` no existe.  
   Solucion: crear `templates/finanzas/analisis/comparativas.html` o actualizar la vista para renderizar una plantilla existente.

3. Error `TypeError` en busquedas AJAX de inventario  
   Ubicacion: `inventario/views.py:627` y `inventario/views.py:1001`  
   Error exacto: `isinstance() arg 2 must be a type...`  
   Causa: uso invalido `isinstance(sucursal, redirect)`.  
   Solucion: reemplazar esa validacion por chequeo de tipo de respuesta (`HttpResponseRedirect`) o por logica booleana explicita.

4. Error `TemplateDoesNotExist` en panel inventario (inventario y movimientos)  
   Ubicacion: `inventario/views.py:705` y `movimientos/views.py:72`  
   Error exacto: falta `inventario/panel_inventario.html`.  
   Estado real de archivos: existe `templates/movimientos/panel_inventario.html`.  
   Solucion: usar `render(..., 'movimientos/panel_inventario.html')` o crear duplicado en `templates/inventario/panel_inventario.html`.

5. Error `FieldError` en alertas de movimientos  
   Ubicacion: `movimientos/views.py:38`  
   Error exacto: `Cannot resolve keyword 'resuelta' into field`  
   Causa: el modelo `AlertaInventario` no tiene campo `resuelta`.  
   Solucion: o agregar campo `resuelta` con migracion, o retirar ese filtro de la consulta.

6. Error `DoesNotExist` no manejado en detalle de factura  
   Ubicacion: `movimientos/views.py:80`  
   Error exacto: `Factura matching query does not exist.`  
   Solucion: reemplazar `Factura.objects.get(id=id)` por `get_object_or_404(Factura, id=id)` o manejar excepcion y devolver 404.

7. Error en signal de usuarios al iniciar sesion (detectado en corrida inicial)  
   Ubicacion: `usuarios/signals.py:30` y `usuarios/emails.py:202`  
   Error exacto: `AttributeError: 'NoneType' object has no attribute 'get_full_name'`  
   Causa: `aprobado_por` puede quedar en `None` y luego se usa sin validar en plantilla/email.  
   Solucion: validar `aprobado_por` antes de usarlo y definir fallback seguro en `enviar_email_aprobacion`.

8. Migraciones pendientes en finanzas  
   Comando: `python manage.py makemigrations --check --dry-run`  
   Salida: se propone `finanzas/migrations/0003_remove_registroasistencia_empleado_and_more.py`.  
   Solucion: generar y aplicar migracion:
   - `python manage.py makemigrations finanzas`
   - `python manage.py migrate`

### Riesgos de seguridad (check --deploy)

Advertencias detectadas:
- `DEBUG=True`
- `SECRET_KEY` debil para produccion
- `SECURE_SSL_REDIRECT` no activo
- `SESSION_COOKIE_SECURE` no activo
- `CSRF_COOKIE_SECURE` no activo
- `SECURE_HSTS_SECONDS` no configurado

Solucion recomendada (produccion):
- mover secretos a variables de entorno
- `DEBUG=False`
- habilitar cookies seguras, HSTS y redireccion SSL

### Comandos para reproducir QA

```powershell
cd C:\Users\DANIE\SISBAR1.1_AFTM-SAS
.\venv\Scripts\Activate.ps1

python manage.py test usuarios.test_backend_qa -v 2
python manage.py test -v 2
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
```
