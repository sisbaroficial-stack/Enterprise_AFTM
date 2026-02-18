"""
VISTAS AVANZADAS - NÓMINA Y EMPLEADOS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from decimal import Decimal

from finanzas.models import Empleado, Nomina, Asistencia, Vacacion
from finanzas.services.nomina_colombia import CalculadoraNomina
from finanzas.services.exportador import ExportadorPDF


@login_required
def lista_empleados_completa(request):
    """Lista completa de empleados con funcionalidades"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('dashboard:home')
    
    # Filtrar por sucursal si es ADMIN
    if request.user.rol == 'ADMIN':
        empleados = Empleado.objects.filter(
            sucursal=request.user.sucursal,
            estado__in=['ACTIVO', 'VACACIONES', 'LICENCIA']
        )
    else:
        empleados = Empleado.objects.filter(
            estado__in=['ACTIVO', 'VACACIONES', 'LICENCIA']
        )
    
    empleados = empleados.order_by('sucursal', 'apellidos')
    
    # Estadísticas
    total_empleados = empleados.count()
    total_nomina = sum([e.salario_base for e in empleados])
    
    context = {
        'empleados': empleados,
        'total_empleados': total_empleados,
        'total_nomina': total_nomina,
    }
    
    return render(request, 'finanzas/empleados/lista_completa.html', context)


@login_required
def crear_empleado_completo(request):
    """Crear nuevo empleado"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        try:
            from sucursales.models import Sucursal
            
            empleado = Empleado.objects.create(
                tipo_documento=request.POST.get('tipo_documento'),
                numero_documento=request.POST.get('numero_documento'),
                nombres=request.POST.get('nombres'),
                apellidos=request.POST.get('apellidos'),
                fecha_nacimiento=request.POST.get('fecha_nacimiento'),
                telefono=request.POST.get('telefono'),
                email=request.POST.get('email', ''),
                direccion=request.POST.get('direccion'),
                ciudad=request.POST.get('ciudad', 'Bogotá'),
                cargo=request.POST.get('cargo'),
                sucursal_id=request.POST.get('sucursal'),
                tipo_contrato=request.POST.get('tipo_contrato'),
                fecha_ingreso=request.POST.get('fecha_ingreso'),
                salario_base=Decimal(request.POST.get('salario_base')),
                auxilio_transporte=Decimal(request.POST.get('auxilio_transporte', 162000)),
                estado='ACTIVO',
                creado_por=request.user,
            )
            
            messages.success(request, f'✅ Empleado {empleado.nombre_completo} creado exitosamente')
            return redirect('finanzas:lista_empleados')
            
        except Exception as e:
            messages.error(request, f'❌ Error al crear empleado: {str(e)}')
    
    from sucursales.models import Sucursal
    sucursales = Sucursal.objects.filter(activa=True)
    
    context = {
        'sucursales': sucursales,
    }
    
    return render(request, 'finanzas/empleados/crear_completo.html', context)


@login_required
def generar_nomina_completa(request):
    """Genera nómina del mes para todos los empleados"""
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ Solo SUPER_ADMIN puede generar nómina')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        mes = int(request.POST.get('mes'))
        anio = int(request.POST.get('anio'))
        
        # Obtener empleados activos
        empleados = Empleado.objects.filter(estado='ACTIVO')
        
        # Generar nóminas
        nominas_generadas = CalculadoraNomina.generar_nomina_masiva(
            empleados, mes, anio
        )
        
        if nominas_generadas:
            total = sum([n.neto_pagar for n in nominas_generadas])
            messages.success(
                request,
                f'✅ {len(nominas_generadas)} nóminas generadas. Total: ${total:,.0f}'
            )
        else:
            messages.warning(request, '⚠️ Ya existe nómina para este período')
        
        return redirect('finanzas:lista_nominas')
    
    # GET - Mostrar formulario
    ahora = datetime.now()
    
    context = {
        'mes_actual': ahora.month,
        'anio_actual': ahora.year,
    }
    
    return render(request, 'finanzas/nomina/generar_completa.html', context)


@login_required
def lista_nominas_completa(request):
    """Lista de nóminas generadas"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('dashboard:home')
    
    # Filtrar nóminas
    nominas = Nomina.objects.all().select_related('empleado').order_by('-anio', '-mes', 'empleado__apellidos')
    
    if request.user.rol == 'ADMIN':
        nominas = nominas.filter(empleado__sucursal=request.user.sucursal)
    
    # Filtros
    mes_filtro = request.GET.get('mes')
    anio_filtro = request.GET.get('anio')
    
    if mes_filtro:
        nominas = nominas.filter(mes=mes_filtro)
    if anio_filtro:
        nominas = nominas.filter(anio=anio_filtro)
    
    # Estadísticas
    total_nominas = nominas.count()
    total_neto = sum([n.neto_pagar for n in nominas])
    total_costo = sum([n.costo_total_empresa for n in nominas])
    
    context = {
        'nominas': nominas[:100],  # Limitar a 100
        'total_nominas': total_nominas,
        'total_neto': total_neto,
        'total_costo': total_costo,
    }
    
    return render(request, 'finanzas/nomina/lista_completa.html', context)


@login_required
def detalle_nomina_completa(request, nomina_id):
    """Detalle de una nómina"""
    nomina = get_object_or_404(Nomina, id=nomina_id)
    
    # Verificar permisos
    if request.user.rol == 'ADMIN' and nomina.empleado.sucursal != request.user.sucursal:
        messages.error(request, '⛔ Sin permisos')
        return redirect('finanzas:lista_nominas')
    
    context = {
        'nomina': nomina,
    }
    
    return render(request, 'finanzas/nomina/detalle_completa.html', context)


@login_required
def descargar_desprendible(request, nomina_id):
    """Descarga desprendible de pago en PDF"""
    nomina = get_object_or_404(Nomina, id=nomina_id)
    
    # Verificar permisos
    if request.user.rol == 'ADMIN' and nomina.empleado.sucursal != request.user.sucursal:
        messages.error(request, '⛔ Sin permisos')
        return redirect('finanzas:lista_nominas')
    
    try:
        return ExportadorPDF.exportar_desprendible_nomina(nomina)
    except ImportError:
        messages.error(request, '⚠️ Instala: pip install reportlab')
        return redirect('finanzas:detalle_nomina', nomina_id=nomina_id)


@login_required
def marcar_nomina_pagada(request, nomina_id):
    """Marca una nómina como pagada"""
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ Solo SUPER_ADMIN puede marcar como pagado')
        return redirect('finanzas:lista_nominas')
    
    nomina = get_object_or_404(Nomina, id=nomina_id)
    
    nomina.pagado = True
    nomina.fecha_pago = datetime.now().date()
    nomina.save()
    
    messages.success(request, f'✅ Nómina de {nomina.empleado.nombre_completo} marcada como pagada')
    
    return redirect('finanzas:lista_nominas')


# ===== AGREGAR ESTAS VISTAS A urls.py =====
"""
# En finanzas/urls.py agregar:

# Empleados avanzado
path('empleados/completa/', views_avanzadas.lista_empleados_completa, name='lista_empleados_completa'),
path('empleados/crear/completo/', views_avanzadas.crear_empleado_completo, name='crear_empleado_completo'),

# Nómina avanzado
path('nomina/completa/', views_avanzadas.lista_nominas_completa, name='lista_nominas_completa'),
path('nomina/generar/completa/', views_avanzadas.generar_nomina_completa, name='generar_nomina_completa'),
path('nomina/<int:nomina_id>/completa/', views_avanzadas.detalle_nomina_completa, name='detalle_nomina_completa'),
path('nomina/<int:nomina_id>/desprendible/', views_avanzadas.descargar_desprendible, name='descargar_desprendible'),
path('nomina/<int:nomina_id>/marcar-pagada/', views_avanzadas.marcar_nomina_pagada, name='marcar_nomina_pagada'),
"""