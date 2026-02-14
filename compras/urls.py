from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    # Sugerencias
    path('', views.sugerencias_compra, name='sugerencias_compra'),
    path('<int:sugerencia_id>/', views.detalle_sugerencia, name='detalle_sugerencia'),
    
    # Exportar
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
    
    # Configuración
    path('configuracion/', views.configuracion_compras, name='configuracion'),
]