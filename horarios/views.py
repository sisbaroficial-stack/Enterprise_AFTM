from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import PlantillaHorario, DiaHorario, AsignacionHorario
from usuarios.models import Usuario

DIAS_SEMANA = [0, 1, 2, 3, 4, 5, 6]
NOMBRES_DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def es_super_admin(user):
    return user.rol == 'SUPER_ADMIN'


def es_admin_o_superior(user):
    return user.rol in ['SUPER_ADMIN', 'ADMIN']


# ─────────────────────────────────────────────
# VISTAS PARA SUPER ADMIN — PLANTILLAS
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_super_admin)
def lista_plantillas(request):
    plantillas = PlantillaHorario.objects.prefetch_related('dias').all()
    return render(request, 'horarios/lista_plantillas.html', {'plantillas': plantillas})


@login_required
@user_passes_test(es_super_admin)
def crear_plantilla(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        color = request.POST.get('color', '#4e73df')

        if not nombre:
            messages.error(request, '❌ El nombre del turno es obligatorio.')
            return redirect('horarios:crear_plantilla')

        plantilla = PlantillaHorario.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            color=color,
            creado_por=request.user
        )

        # Guardar los 7 días
        for i in range(7):
            es_descanso = request.POST.get(f'descanso_{i}') == 'on'
            hora_entrada = request.POST.get(f'entrada_{i}') or None
            hora_salida = request.POST.get(f'salida_{i}') or None

            DiaHorario.objects.create(
                plantilla=plantilla,
                dia_semana=i,
                es_descanso=es_descanso,
                hora_entrada=None if es_descanso else hora_entrada,
                hora_salida=None if es_descanso else hora_salida,
            )

        messages.success(request, f'✅ Plantilla "{nombre}" creada correctamente.')
        return redirect('horarios:lista_plantillas')

    context = {'dias': NOMBRES_DIAS, 'indices': range(7)}
    return render(request, 'horarios/crear_plantilla.html', context)


@login_required
@user_passes_test(es_super_admin)
def editar_plantilla(request, plantilla_id):
    plantilla = get_object_or_404(PlantillaHorario, id=plantilla_id)
    dias = {d.dia_semana: d for d in plantilla.dias.all()}

    if request.method == 'POST':
        plantilla.nombre = request.POST.get('nombre', '').strip()
        plantilla.descripcion = request.POST.get('descripcion', '').strip()
        plantilla.color = request.POST.get('color', '#4e73df')
        plantilla.save()

        for i in range(7):
            es_descanso = request.POST.get(f'descanso_{i}') == 'on'
            hora_entrada = request.POST.get(f'entrada_{i}') or None
            hora_salida = request.POST.get(f'salida_{i}') or None

            dia, _ = DiaHorario.objects.get_or_create(plantilla=plantilla, dia_semana=i)
            dia.es_descanso = es_descanso
            dia.hora_entrada = None if es_descanso else hora_entrada
            dia.hora_salida = None if es_descanso else hora_salida
            dia.save()

        messages.success(request, f'✅ Plantilla "{plantilla.nombre}" actualizada.')
        return redirect('horarios:lista_plantillas')

    context = {
        'plantilla': plantilla,
        'dias': NOMBRES_DIAS,
        'indices': range(7),
        'dias_data': dias,
    }
    return render(request, 'horarios/editar_plantilla.html', context)


@login_required
@user_passes_test(es_super_admin)
def eliminar_plantilla(request, plantilla_id):
    plantilla = get_object_or_404(PlantillaHorario, id=plantilla_id)
    if request.method == 'POST':
        nombre = plantilla.nombre
        plantilla.delete()
        messages.success(request, f'🗑️ Plantilla "{nombre}" eliminada.')
        return redirect('horarios:lista_plantillas')
    return render(request, 'horarios/confirmar_eliminar_plantilla.html', {'plantilla': plantilla})


# ─────────────────────────────────────────────
# VISTAS PARA SUPER ADMIN — ASIGNACIONES
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_admin_o_superior)
def lista_asignaciones(request):
    asignaciones = AsignacionHorario.objects.select_related(
        'usuario', 'plantilla'
    ).all()
    return render(request, 'horarios/lista_asignaciones.html', {'asignaciones': asignaciones})


@login_required
@user_passes_test(es_admin_o_superior)
def asignar_horario(request, usuario_id=None):
    usuarios = Usuario.objects.filter(is_active=True, aprobado=True).order_by('first_name')
    plantillas = PlantillaHorario.objects.filter(activo=True)
    usuario_sel = get_object_or_404(Usuario, id=usuario_id) if usuario_id else None

    if request.method == 'POST':
        uid = request.POST.get('usuario')
        pid = request.POST.get('plantilla')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin') or None
        notas = request.POST.get('notas', '')

        usuario = get_object_or_404(Usuario, id=uid)
        plantilla = get_object_or_404(PlantillaHorario, id=pid)

        # Desactivar asignaciones anteriores activas
        AsignacionHorario.objects.filter(usuario=usuario, activo=True).update(activo=False)

        AsignacionHorario.objects.create(
            usuario=usuario,
            plantilla=plantilla,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            notas=notas,
            activo=True,
            asignado_por=request.user
        )

        messages.success(request, f'✅ Horario asignado a {usuario.get_full_name()} correctamente.')
        return redirect('horarios:lista_asignaciones')

    context = {
        'usuarios': usuarios,
        'plantillas': plantillas,
        'usuario_sel': usuario_sel,
        'hoy': timezone.now().date(),
    }
    return render(request, 'horarios/asignar_horario.html', context)


@login_required
@user_passes_test(es_admin_o_superior)
def desactivar_asignacion(request, asignacion_id):
    asignacion = get_object_or_404(AsignacionHorario, id=asignacion_id)
    if request.method == 'POST':
        asignacion.activo = False
        asignacion.save()
        messages.warning(request, f'Asignación de {asignacion.usuario.get_full_name()} desactivada.')
    return redirect('horarios:lista_asignaciones')


# ─────────────────────────────────────────────
# VISTA PARA EL EMPLEADO — Ver su horario
# ─────────────────────────────────────────────

@login_required
def mi_horario(request):
    asignacion = AsignacionHorario.objects.filter(
        usuario=request.user, activo=True
    ).select_related('plantilla').prefetch_related('plantilla__dias').first()

    dias_semana = []
    if asignacion:
        dias_db = {d.dia_semana: d for d in asignacion.plantilla.dias.all()}
        for i, nombre in enumerate(NOMBRES_DIAS):
            dia = dias_db.get(i)
            dias_semana.append({
                'nombre': nombre,
                'indice': i,
                'dia': dia,
            })

    context = {
        'asignacion': asignacion,
        'dias_semana': dias_semana,
    }
    return render(request, 'horarios/mi_horario.html', context)