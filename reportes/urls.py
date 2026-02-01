
from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.reportes_home_view, name='home'),
    path('exportar/productos/excel/', views.exportar_productos_excel, name='exportar_productos_excel'),
    path('exportar/movimientos/excel/', views.exportar_movimientos_excel, name='exportar_movimientos_excel'),
        # ✅ NUEVOS REPORTES
    path('abc/', views.reporte_abc, name='reporte_abc'),
    path('rotacion/', views.reporte_rotacion, name='reporte_rotacion'),
    path('sin-movimiento/', views.reporte_sin_movimiento, name='sin_movimiento'),
]