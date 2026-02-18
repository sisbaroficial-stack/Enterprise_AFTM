from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from .models import Notificacion


@login_required
def api_notificaciones_recientes(request):
    """API para obtener notificaciones recientes"""
    if request.user.rol != 'SUPER_ADMIN':
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    notificaciones = Notificacion.objects.all()[:20]
    no_leidas = Notificacion.objects.filter(leida=False).count()
    
    def tiempo_desde(fecha):
        ahora = timezone.now()
        diff = ahora - fecha
        
        if diff.days > 0:
            return f'Hace {diff.days} día{"s" if diff.days > 1 else ""}'
        elif diff.seconds > 3600:
            return f'Hace {diff.seconds // 3600} hora{"s" if diff.seconds // 3600 > 1 else ""}'
        elif diff.seconds > 60:
            return f'Hace {diff.seconds // 60} minuto{"s" if diff.seconds // 60 > 1 else ""}'
        else:
            return 'Ahora mismo'
    
    data = {
        'no_leidas': no_leidas,
        'notificaciones': [
            {
                'id': n.id,
                'tipo': n.tipo,
                'titulo': n.titulo,
                'mensaje': n.mensaje,
                'sucursal': n.sucursal.nombre if n.sucursal else None,
                'leida': n.leida,
                'tiempo_transcurrido': tiempo_desde(n.fecha_creacion),
                'monto': float(n.monto) if n.monto else None,
            }
            for n in notificaciones
        ]
    }
    
    return JsonResponse(data)


@login_required
def marcar_leida(request, notif_id):
    """Marcar notificación como leída"""
    if request.user.rol != 'SUPER_ADMIN':
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    notif = get_object_or_404(Notificacion, id=notif_id)
    notif.marcar_leida()
    
    if request.method == 'POST':
        return JsonResponse({'success': True})
    else:
        return redirect('notificaciones:todas')


@login_required
def marcar_todas_leidas(request):
    """Marcar todas como leídas"""
    if request.user.rol != 'SUPER_ADMIN':
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method == 'POST':
        Notificacion.objects.filter(leida=False).update(
            leida=True,
            fecha_lectura=timezone.now()
        )
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def todas_notificaciones(request):
    """Vista de todas las notificaciones paginadas"""
    if request.user.rol != 'SUPER_ADMIN':
        return redirect('dashboard:home')

    # Ordenamos por fecha descendente (más recientes primero)
    notificaciones_list = Notificacion.objects.all().order_by('-fecha_creacion')

    # ----- PAGINACION -----
    paginator = Paginator(notificaciones_list, 15)  # 15 notificaciones por página
    page_number = request.GET.get('page')
    notificaciones = paginator.get_page(page_number)
    # ----------------------

    stats = {
        'total': Notificacion.objects.count(),
        'no_leidas': Notificacion.objects.filter(leida=False).count(),
        'hoy': Notificacion.objects.filter(
            fecha_creacion__date=timezone.now().date()
        ).count(),
    }

    context = {
        'notificaciones': notificaciones,
        'stats': stats,
    }

    return render(request, 'notificaciones/todas.html', context)