"""
URLS DEL MÓDULO DE FINANZAS
"""
from . import views_avanzadas

from django.urls import path
from . import views

app_name = 'finanzas'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_finanzas, name='dashboard'),
    
    # Gestión de Gastos
    path('gastos/', views.lista_gastos, name='lista_gastos'),
    path('gastos/registrar/', views.registrar_gasto, name='registrar_gasto'),
    path('gastos/<int:gasto_id>/', views.detalle_gasto, name='detalle_gasto'),
    path('gastos/<int:gasto_id>/aprobar/', views.aprobar_gasto, name='aprobar_gasto'),
    path('gastos/<int:gasto_id>/rechazar/', views.rechazar_gasto, name='rechazar_gasto'),
    path('gastos/<int:gasto_id>/editar/', views.editar_gasto, name='editar_gasto'),
    path('gastos/<int:gasto_id>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),
    
    # Nómina
    path('nomina/', views.lista_nominas, name='lista_nominas'),
    path('nomina/generar/', views.generar_nomina, name='generar_nomina'),
    path('nomina/<int:nomina_id>/', views.detalle_nomina, name='detalle_nomina'),
    path('nomina/<int:nomina_id>/desprendible/', views.desprendible_pago, name='desprendible_pago'),
    
    # Empleados
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/<int:empleado_id>/', views.detalle_empleado, name='detalle_empleado'),
    path('empleados/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    
    # Análisis y Reportes
    path('analisis/', views.analisis_financiero, name='analisis'),
    path('comparativas/', views.comparativas_mensuales, name='comparativas'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
    
    # Manual de Usuario
    path('manual/', views.manual_usuario, name='manual'),
    
    # API para gráficas (AJAX)
    path('api/datos-graficas/<int:mes>/<int:anio>/', views.api_datos_graficas, name='api_datos_graficas'),

        # Empleados completo
    path('empleados/completa/', views_avanzadas.lista_empleados_completa, name='lista_empleados_completa'),
    path('empleados/crear/completo/', views_avanzadas.crear_empleado_completo, name='crear_empleado_completo'),
    
    # Nómina completa
    path('nomina/completa/', views_avanzadas.lista_nominas_completa, name='lista_nominas_completa'),
    path('nomina/generar/completa/', views_avanzadas.generar_nomina_completa, name='generar_nomina_completa'),
    path('nomina/<int:nomina_id>/completa/', views_avanzadas.detalle_nomina_completa, name='detalle_nomina_completa'),
    path('nomina/<int:nomina_id>/desprendible/', views_avanzadas.descargar_desprendible, name='descargar_desprendible'),
    path('nomina/<int:nomina_id>/marcar-pagada/', views_avanzadas.marcar_nomina_pagada, name='marcar_nomina_pagada'),

]
