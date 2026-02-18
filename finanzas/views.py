"""
VISTAS DEL MÓDULO DE FINANZAS - COMPLETO
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
from decimal import Decimal

from .models import Gasto, CategoriaGasto, Empleado, Nomina
from .services.calculador_finanzas import CalculadorFinanzas
from sucursales.models import Sucursal


@login_required
def dashboard_finanzas(request):
    """
    Dashboard principal de finanzas
    Se adapta automáticamente a modo sucursal/global
    """
    # Solo SUPER_ADMIN y ADMIN pueden acceder
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ No tienes permiso para acceder a Finanzas')
        return redirect('dashboard:home')
    
    # Obtener mes actual
    ahora = datetime.now()
    mes_actual = ahora.month
    anio_actual = ahora.year
    
    # Calcular datos financieros
    calculador = CalculadorFinanzas(request)
    datos = calculador.calcular_utilidad_mes(mes_actual, anio_actual)
    comparativa = calculador.comparar_meses(mes_actual, anio_actual, meses_atras=1)
    punto_equilibrio = calculador.calcular_punto_equilibrio(mes_actual, anio_actual)
    
    # Gastos pendientes (solo SUPER_ADMIN)
    gastos_pendientes = None
    if request.user.rol == 'SUPER_ADMIN':
        gastos_pendientes = Gasto.objects.filter(
            estado='PENDIENTE'
        ).select_related('categoria', 'sucursal', 'registrado_por').order_by('-monto')[:10]
    
    context = {
        'datos': datos,
        'comparativa': comparativa,
        'punto_equilibrio': punto_equilibrio,
        'gastos_pendientes': gastos_pendientes,
        'mes_nombre': ahora.strftime('%B'),
        'anio': anio_actual,
        'modo_global': calculador.sucursal_actual is None,
        'sucursal_actual': calculador.sucursal_actual,
    }
    
    return render(request, 'finanzas/dashboard.html', context)


@login_required
def lista_gastos(request):
    """Lista todos los gastos"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return redirect('dashboard:home')
    
    calculador = CalculadorFinanzas(request)
    
    # Filtrar gastos según sucursal
    gastos = Gasto.objects.all().select_related('categoria', 'sucursal', 'registrado_por')
    
    if calculador.sucursal_actual:
        from django.db.models import Q
        gastos = gastos.filter(
            Q(sucursal=calculador.sucursal_actual) |
            Q(sucursal__isnull=True)
        )
    
    gastos = gastos.order_by('-fecha', '-fecha_registro')[:100]
    
    context = {
        'gastos': gastos,
        'modo_global': calculador.sucursal_actual is None,
    }
    
    return render(request, 'finanzas/gastos/lista.html', context)


@login_required
def registrar_gasto(request):
    """Registrar nuevo gasto"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        monto = Decimal(request.POST.get('monto', 0))
        
        # Auto-aprobar si es menor a $100,000
        if monto < Decimal('50000'):
            estado = 'APROBADO'
            aprobado_por = request.user
            fecha_aprobacion = datetime.now()
        else:
            estado = 'PENDIENTE'
            aprobado_por = None
            fecha_aprobacion = None
        
        # Determinar sucursal correctamente
        if request.user.rol == 'ADMIN':
            # Tomar la sucursal del usuario admin
            sucursal_id = request.user.sucursal.id if request.user.sucursal else None
        else:
            # Tomar la sucursal seleccionada en el formulario por SUPER_ADMIN
            sucursal_id = request.POST.get('sucursal') or None
        
        # Crear gasto
        gasto = Gasto.objects.create(
            fecha=request.POST.get('fecha'),
            sucursal_id=sucursal_id,  # <-- ahora siempre es un ID o None
            categoria_id=request.POST.get('categoria'),
            concepto=request.POST.get('concepto'),
            monto=monto,
            metodo_pago=request.POST.get('metodo_pago'),
            notas=request.POST.get('notas', ''),
            estado=estado,
            registrado_por=request.user,
            aprobado_por=aprobado_por,
            fecha_aprobacion=fecha_aprobacion,
        )
        # ====== CREAR NOTIFICACIÓN SI ES PENDIENTE ======
        if estado == 'PENDIENTE':
            try:
                from notificaciones.models import Notificacion
                Notificacion.crear_notificacion(
                    tipo='GASTO_PENDIENTE',
                    titulo=f'⏳ Gasto Pendiente - ${monto:,.0f}',
                    mensaje=f'{request.user.get_full_name()} registró un gasto de ${monto:,.0f} que requiere aprobación. Concepto: {gasto.concepto}',
                    sucursal=gasto.sucursal,
                    usuario=request.user,
                    monto=monto,
                    ref_id=gasto.id,
                    ref_tipo='gasto'
                )
            except:
                pass
        
        # Mensajes
        if estado == 'APROBADO':
            messages.success(request, f'✅ Gasto registrado y aprobado automáticamente (${monto:,.0f})')
        else:
            messages.info(request, f'⏳ Gasto registrado. Pendiente de aprobación por SUPER_ADMIN (${monto:,.0f})')
        
        return redirect('finanzas:lista_gastos')
    
    # GET - Mostrar formulario
    categorias = CategoriaGasto.objects.filter(activa=True).order_by('orden', 'nombre')
    sucursales = Sucursal.objects.filter(activa=True) if request.user.rol == 'SUPER_ADMIN' else []
    
    context = {
        'categorias': categorias,
        'sucursales': sucursales,
        'es_admin': request.user.rol == 'ADMIN',
        'today': datetime.now().date(),
    }
    
    return render(request, 'finanzas/gastos/registrar.html', context)



@login_required
def aprobar_gasto(request, gasto_id):
    """Aprobar un gasto pendiente"""
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ Solo SUPER_ADMIN puede aprobar gastos')
        return redirect('finanzas:lista_gastos')
    
    gasto = get_object_or_404(Gasto, id=gasto_id)
    gasto.aprobar(request.user)
    
    messages.success(request, f'✅ Gasto aprobado: {gasto.concepto} (${gasto.monto:,.0f})')
    return redirect('finanzas:dashboard')


@login_required
def rechazar_gasto(request, gasto_id):
    """Rechazar un gasto pendiente"""
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ Solo SUPER_ADMIN puede rechazar gastos')
        return redirect('finanzas:lista_gastos')
    
    gasto = get_object_or_404(Gasto, id=gasto_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', 'No especificado')
        gasto.rechazar(request.user, motivo)
        
        messages.warning(request, f'❌ Gasto rechazado: {gasto.concepto}')
        return redirect('finanzas:dashboard')
    
    return render(request, 'finanzas/gastos/rechazar.html', {'gasto': gasto})


@login_required
def detalle_gasto(request, gasto_id):
    """Detalle de un gasto"""
    gasto = get_object_or_404(Gasto, id=gasto_id)
    return render(request, 'finanzas/gastos/detalle.html', {'gasto': gasto})


@login_required
def editar_gasto(request, gasto_id):
    """Editar gasto"""
    messages.info(request, '⚠️ Funcionalidad en desarrollo')
    return redirect('finanzas:lista_gastos')


@login_required
def eliminar_gasto(request, gasto_id):
    """Eliminar gasto"""
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ Solo SUPER_ADMIN puede eliminar gastos')
        return redirect('finanzas:lista_gastos')
    
    gasto = get_object_or_404(Gasto, id=gasto_id)
    concepto = gasto.concepto
    gasto.delete()
    messages.success(request, f'🗑️ Gasto eliminado: {concepto}')
    return redirect('finanzas:lista_gastos')


# ========== EMPLEADOS ==========

@login_required
def lista_empleados(request):
    """Lista completa de empleados"""
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
    
    empleados = empleados.select_related('sucursal').order_by('sucursal', 'apellidos')
    
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
def crear_empleado(request):
    """Crear nuevo empleado"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('dashboard:home')

    if request.method == 'POST':
        try:
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
            # ====== CREAR NOTIFICACIÓN ======
            try:
                from notificaciones.models import Notificacion
                Notificacion.crear_notificacion(
                    tipo='EMPLEADO_CREADO',
                    titulo=f'👤 Empleado Creado: {empleado.nombre_completo}',
                    mensaje=f'{request.user.get_full_name()} creó el empleado "{empleado.nombre_completo}" - {empleado.cargo}',
                    sucursal=empleado.sucursal,
                    usuario=request.user,
                    ref_id=empleado.id,
                    ref_tipo='empleado'
                )
            except:
                pass
            
            messages.success(request, f'✅ Empleado {empleado.nombre_completo} creado exitosamente')
            return redirect('finanzas:lista_empleados')
            
        except Exception as e:
            messages.error(request, f'❌ Error al crear empleado: {str(e)}')
    
    # GET - mostrar formulario
    if request.user.rol == 'SUPER_ADMIN':
        sucursales = Sucursal.objects.filter(activa=True).order_by('nombre')
    else:
        sucursales = [request.user.sucursal] if request.user.sucursal else []

    context = {
        'sucursales': sucursales,
    }

    return render(request, 'finanzas/empleados/crear_completo.html', context)


@login_required
def detalle_empleado(request, empleado_id):
    """Detalle de empleado"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    context = {'empleado': empleado}
    return render(request, 'finanzas/empleados/detalle_empleado.html', context)


@login_required
def editar_empleado(request, empleado_id):
    """Editar empleado existente"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('finanzas:lista_empleados')
    
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # Verificar que ADMIN solo edite empleados de su sucursal
    if request.user.rol == 'ADMIN' and empleado.sucursal != request.user.sucursal:
        messages.error(request, '⛔ Solo puedes editar empleados de tu sucursal')
        return redirect('finanzas:lista_empleados')
    
    if request.method == 'POST':
        try:
            # Actualizar datos
            empleado.tipo_documento = request.POST.get('tipo_documento')
            empleado.numero_documento = request.POST.get('numero_documento')
            empleado.nombres = request.POST.get('nombres')
            empleado.apellidos = request.POST.get('apellidos')
            empleado.fecha_nacimiento = request.POST.get('fecha_nacimiento')
            empleado.telefono = request.POST.get('telefono')
            empleado.email = request.POST.get('email', '')
            empleado.direccion = request.POST.get('direccion')
            empleado.ciudad = request.POST.get('ciudad')
            empleado.cargo = request.POST.get('cargo')
            empleado.tipo_contrato = request.POST.get('tipo_contrato')
            empleado.salario_base = Decimal(request.POST.get('salario_base'))
            empleado.auxilio_transporte = Decimal(request.POST.get('auxilio_transporte', 162000))
            empleado.estado = request.POST.get('estado', 'ACTIVO')
            
            # Solo SUPER_ADMIN puede cambiar de sucursal
            if request.user.rol == 'SUPER_ADMIN':
                empleado.sucursal_id = request.POST.get('sucursal')
            
            empleado.save()
            
            messages.success(request, f'✅ Empleado {empleado.nombre_completo} actualizado exitosamente')
            return redirect('finanzas:detalle_empleado', empleado_id=empleado.id)
            
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar empleado: {str(e)}')
    
    # GET - mostrar formulario
    if request.user.rol == 'SUPER_ADMIN':
        sucursales = Sucursal.objects.filter(activa=True).order_by('nombre')
    else:
        sucursales = [request.user.sucursal] if request.user.sucursal else []
    
    context = {
        'empleado': empleado,
        'sucursales': sucursales,
    }
    
    return render(request, 'finanzas/empleados/editar.html', context)


# ========== NÓMINA ==========

@login_required
def lista_nominas(request):
    """Lista de nóminas generadas"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('dashboard:home')
    
    # Filtrar nóminas
    nominas = Nomina.objects.all().select_related('empleado', 'empleado__sucursal').order_by('-anio', '-mes', 'empleado__apellidos')
    
    if request.user.rol == 'ADMIN':
        nominas = nominas.filter(empleado__sucursal=request.user.sucursal)
    
    # Filtros opcionales
    mes_filtro = request.GET.get('mes')
    anio_filtro = request.GET.get('anio')
    
    if mes_filtro:
        nominas = nominas.filter(mes=mes_filtro)
    if anio_filtro:
        nominas = nominas.filter(anio=anio_filtro)
    
    # Limitar a 100 registros
    nominas = nominas[:100]
    
    # Estadísticas
    total_nominas = nominas.count()
    total_neto = sum([n.neto_pagar for n in nominas])
    total_costo = sum([n.costo_total_empresa for n in nominas])
    
    context = {
        'nominas': nominas,
        'total_nominas': total_nominas,
        'total_neto': total_neto,
        'total_costo': total_costo,
    }
    
    return render(request, 'finanzas/nomina/lista_completa.html', context)


"""
VISTA ACTUALIZADA: Generar Nómina con Auto-Crear Gasto
"""

@login_required
def generar_nomina(request):
    """
    Genera nómina del mes para todos los empleados
    Y CREA AUTOMÁTICAMENTE EL GASTO en finanzas
    """
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ Solo SUPER_ADMIN puede generar nómina')
        return redirect('finanzas:lista_nominas')
    
    if request.method == 'POST':
        from .services.nomina_colombia import CalculadoraNomina
        from decimal import Decimal
        
        mes = int(request.POST.get('mes'))
        anio = int(request.POST.get('anio'))
        
        # Obtener empleados activos
        empleados = Empleado.objects.filter(estado='ACTIVO')
        
        if not empleados.exists():
            messages.warning(request, '⚠️ No hay empleados activos para generar nómina')
            return redirect('finanzas:lista_nominas')
        
        # Generar nóminas
        nominas_generadas = CalculadoraNomina.generar_nomina_masiva(
            empleados, mes, anio
        )
        
        if nominas_generadas:
            # Calcular total
            total_neto = sum([n.neto_pagar for n in nominas_generadas])
            total_costo_empresa = sum([n.costo_total_empresa for n in nominas_generadas])
            
            # ====== CREAR GASTO AUTOMÁTICO DE NÓMINA ======
            try:
                # Buscar categoría "Nómina y Personal"
                categoria_nomina = CategoriaGasto.objects.filter(
                    nombre__icontains='nómina'
                ).first()
                
                if not categoria_nomina:
                    categoria_nomina = CategoriaGasto.objects.filter(
                        nombre__icontains='personal'
                    ).first()
                
                if categoria_nomina:
                    # Crear el gasto (se aprueba automáticamente)
                    gasto_nomina = Gasto.objects.create(
                        fecha=datetime.now().date(),
                        sucursal=None,  # Gasto general (todas las sucursales)
                        categoria=categoria_nomina,
                        concepto=f'Nómina {mes}/{anio} - {len(nominas_generadas)} empleados',
                        monto=total_costo_empresa,  # Costo total para empresa (incluye aportes)
                        metodo_pago='TRANSFERENCIA',
                        notas=f'Gasto generado automáticamente al generar nómina. Neto pagado: ${total_neto:,.0f}. Total con aportes: ${total_costo_empresa:,.0f}',
                        estado='APROBADO',  # Se aprueba automáticamente
                        registrado_por=request.user,
                        aprobado_por=request.user,
                        fecha_aprobacion=datetime.now(),
                    )
                    
                    messages.success(
                        request,
                        f'✅ {len(nominas_generadas)} nóminas generadas exitosamente.<br>'
                        f'💰 Total neto: ${total_neto:,.0f}<br>'
                        f'📊 Total costo empresa: ${total_costo_empresa:,.0f}<br>'
                        f'💸 <strong>Gasto de nómina creado automáticamente</strong>'
                    )
                else:
                    messages.success(
                        request,
                        f'✅ {len(nominas_generadas)} nóminas generadas.<br>'
                        f'⚠️ No se pudo crear el gasto automático (categoría Nómina no encontrada)'
                    )
            
            except Exception as e:
                messages.warning(
                    request,
                    f'✅ Nóminas generadas correctamente.<br>'
                    f'⚠️ Error al crear gasto automático: {str(e)}'
                )
            
            # ====== CREAR NOTIFICACIÓN ======
            try:
                from finanzas.models import Notificacion
                Notificacion.crear_notificacion(
                    tipo='NOMINA_GENERADA',
                    titulo=f'💰 Nómina {mes}/{anio} Generada',
                    mensaje=f'{len(nominas_generadas)} nóminas generadas. Total: ${total_costo_empresa:,.0f}',
                    usuario=request.user,
                    monto=total_costo_empresa,
                )
            except:
                pass  # Si no existe el modelo de notificaciones, continuar
        
        else:
            messages.warning(request, '⚠️ Ya existe nómina para este período o no se pudo generar')
        
        return redirect('finanzas:lista_nominas')
    
    # GET - Mostrar formulario
    ahora = datetime.now()
    
    context = {
        'mes_actual': ahora.month,
        'anio_actual': ahora.year,
    }
    
    return render(request, 'finanzas/nomina/generar_completa.html', context)

@login_required
def detalle_nomina(request, nomina_id):
    """Detalle de una nómina"""
    nomina = get_object_or_404(Nomina, id=nomina_id)
    
    # Verificar permisos
    if request.user.rol == 'ADMIN' and nomina.empleado.sucursal != request.user.sucursal:
        messages.error(request, '⛔ Sin permisos para ver esta nómina')
        return redirect('finanzas:lista_nominas')
    
    context = {
        'nomina': nomina,
    }
    
    return render(request, 'finanzas/nomina/detalle_completa.html', context)


@login_required
def desprendible_pago(request, nomina_id):
    """Descarga desprendible de pago en PDF"""
    nomina = get_object_or_404(Nomina, id=nomina_id)
    
    # Verificar permisos
    if request.user.rol == 'ADMIN' and nomina.empleado.sucursal != request.user.sucursal:
        messages.error(request, '⛔ Sin permisos')
        return redirect('finanzas:lista_nominas')
    
    try:
        from .services.exportador import ExportadorPDF
        return ExportadorPDF.exportar_desprendible_nomina(nomina)
    except ImportError:
        messages.error(request, '⚠️ Instala: pip install reportlab')
        return redirect('finanzas:detalle_nomina', nomina_id=nomina_id)


@login_required
def marcar_nomina_pagada(request, nomina_id):
    """Marcar una nómina como pagada"""
    if request.user.rol != 'SUPER_ADMIN':
        messages.error(request, '⛔ Solo SUPER_ADMIN puede marcar como pagado')
        return redirect('finanzas:lista_nominas')
    
    nomina = get_object_or_404(Nomina, id=nomina_id)
    
    if nomina.pagado:
        messages.warning(request, '⚠️ Esta nómina ya estaba marcada como pagada')
    else:
        nomina.pagado = True
        nomina.fecha_pago = datetime.now().date()
        nomina.save()
        messages.success(request, f'✅ Nómina de {nomina.empleado.nombre_completo} marcada como PAGADA')
    
    return redirect('finanzas:lista_nominas')


# ========== ANÁLISIS CON IA ==========

@login_required
def analisis_financiero(request):
    """Vista avanzada de análisis con IA"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('dashboard:home')
    
    try:
        from .services.ia_predictor import AnalizadorIA
        
        calculador = CalculadorFinanzas(request)
        ahora = datetime.now()
        datos = calculador.calcular_utilidad_mes(ahora.month, ahora.year)
        
        # Análisis con IA
        analizador = AnalizadorIA(sucursal=calculador.sucursal_actual)
        
        # Predicciones
        predicciones = analizador.predecir_gastos_proximos_meses(meses=3)
        
        # Anomalías
        anomalias = analizador.detectar_anomalias_gastos(meses_atras=6)
        
        # Tendencias
        tendencias = analizador.analizar_tendencias_categorias(meses=6)
        
        # Recomendaciones
        recomendaciones = analizador.generar_recomendaciones()
        
        # Score de salud financiera
        scoring = analizador.calcular_scoring_salud_financiera()
        
        context = {
            'datos': datos,
            'predicciones': predicciones,
            'anomalias': anomalias,
            'tendencias': tendencias,
            'recomendaciones': recomendaciones,
            'scoring': scoring,
        }
        
        return render(request, 'finanzas/analisis/principal.html', context)
        
    except ImportError:
        messages.warning(request, '⚠️ Instala Prophet para usar IA: pip install prophet')
        return redirect('finanzas:dashboard')


@login_required
def comparativas_mensuales(request):
    """Comparativas mensuales"""
    return render(request, 'finanzas/analisis/comparativas.html')


# ========== EXPORTACIÓN ==========

@login_required
def exportar_excel(request):
    """Exporta reporte a Excel"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('finanzas:dashboard')
    
    try:
        from .services.exportador import ExportadorExcel
        
        calculador = CalculadorFinanzas(request)
        ahora = datetime.now()
        datos = calculador.calcular_utilidad_mes(ahora.month, ahora.year)
        
        return ExportadorExcel.exportar_reporte_financiero(
            datos, ahora.month, ahora.year
        )
    except ImportError:
        messages.error(request, '⚠️ Instala openpyxl: pip install openpyxl')
        return redirect('finanzas:dashboard')


@login_required
def exportar_pdf(request):
    """Exporta reporte a PDF"""
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, '⛔ Sin permisos')
        return redirect('finanzas:dashboard')
    
    try:
        from .services.exportador import ExportadorPDF
        
        calculador = CalculadorFinanzas(request)
        ahora = datetime.now()
        datos = calculador.calcular_utilidad_mes(ahora.month, ahora.year)
        
        return ExportadorPDF.exportar_reporte_financiero(
            datos, ahora.month, ahora.year
        )
    except ImportError:
        messages.error(request, '⚠️ Instala reportlab: pip install reportlab')
        return redirect('finanzas:dashboard')


# ========== OTROS ==========

@login_required
def manual_usuario(request):
    """Manual de usuario interactivo"""
    return render(request, 'finanzas/manual/guia.html')


@login_required
def api_datos_graficas(request, mes, anio):
    """API para obtener datos de gráficas (AJAX)"""
    calculador = CalculadorFinanzas(request)
    datos = calculador.calcular_utilidad_mes(mes, anio)
    
    # Convertir Decimal a float para JSON
    datos_json = {
        'ventas': float(datos['total_ventas']),
        'costos': float(datos['costo_mercancia']),
        'gastos': float(datos['total_gastos']),
        'utilidad_neta': float(datos['utilidad_neta']),
        'margen_neto': float(datos['margen_neto']),
        'gastos_por_categoria': [
            {
                'categoria': cat['categoria'].nombre,
                'total': float(cat['total']),
                'porcentaje': float(cat['porcentaje']),
            }
            for cat in datos['gastos_por_categoria']
        ]
    }
    
    return JsonResponse(datos_json)