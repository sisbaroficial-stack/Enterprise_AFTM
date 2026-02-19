from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views  # Tu index_view

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Página principal / login
    path('', views.index_view, name='index'),
    path('index/', views.index_view, name='index'),

    # Apps
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),  
    path('inventario/', include('inventario.urls', namespace='inventario')),
    path('categorias/', include('categorias.urls', namespace='categorias')),
    path('proveedores/', include('proveedores.urls', namespace='proveedores')),
    path('movimientos/', include('movimientos.urls', namespace='movimientos')),
    path('facturas/', include('facturas.urls', namespace='facturas')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('sucursales/', include('sucursales.urls', namespace='sucursales')),
    path('compras/', include('compras.urls', namespace='compras')),
    path('finanzas/', include('finanzas.urls', namespace='finanzas')),
    path('notificaciones/', include('notificaciones.urls', namespace='notificaciones')),
    path('horarios/', include('horarios.urls', namespace='horarios')),
]

# Media & Static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin style
admin.site.site_header = "🛒 SISBAR  - Administración"
admin.site.site_title = "SISBAR Admin"
admin.site.index_title = "Panel de Administración"
