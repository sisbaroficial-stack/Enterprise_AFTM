# ========== IMPORTS (TODO AL INICIO) ==========

# Django shortcuts y utilidades
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect

# Autenticación y usuarios
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, Permission

# Formularios y validaciones
from django.views.decorators.http import require_POST
from django.contrib import messages
from sucursales.models import Sucursal

# Core y utilidades
from django.utils import timezone
from django.db.models import Q
from django.db.models.deletion import ProtectedError

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

# Modelos propios
from .models import Usuario, HistorialActividad
from .forms import (
    RegistroUsuarioForm,
    LoginForm,
    PerfilUsuarioForm,
    CambiarPasswordForm,
    AprobarUsuarioForm
)
from .emails import enviar_email_registro, enviar_email_aprobacion, enviar_email_alerta_admin

# Otros apps
from inventario.models import Producto
from categorias.models import Categoria
from proveedores.models import Proveedor

from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

# ========== FUNCIONES AUXILIARES ==========
def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def registrar_actividad(usuario, tipo, descripcion, request=None):
    """Registra una actividad del usuario"""
    ip = get_client_ip(request) if request else None
    HistorialActividad.objects.create(
        usuario=usuario,
        tipo=tipo,
        descripcion=descripcion,
        ip_address=ip
    )


def es_admin(user):
    """Verifica si el usuario es administrador"""
    return user.rol in ['SUPER_ADMIN', 'ADMIN']


# ========== VISTAS DE AUTENTICACIÓN ==========
def registro_view(request):
    """Registro de usuarios con manejo completo de errores"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = RegistroUsuarioForm(request.POST or None)

    if request.method == 'POST':
        try:
            if form.is_valid():
                # Crear usuario pero no aprobar aún
                usuario = form.save(commit=False)
                usuario.aprobado = False  # requiere aprobación
                usuario.is_active = True
                usuario.save()

                # Registrar actividad
                registrar_actividad(
                    usuario,
                    'CREAR',
                    f'Usuario {usuario.username} se registró',
                    request
                )

                # Enviar emails (opcional)
                # enviar_email_registro(usuario)
                # enviar_email_alerta_admin(usuario)

                messages.success(
                    request,
                    '✅ Registro exitoso. Recibirás un correo cuando tu cuenta sea aprobado.'
                )
                return redirect('usuarios:login')
            else:
                # Mostrar errores del formulario en consola y en mensajes
                print("Errores del formulario:", form.errors)
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')

        except Exception as e:
            # Captura cualquier excepción inesperada
            messages.error(request, f'Ocurrió un error inesperado: {e}')
            print("Excepción en registro_view:", e)

    # Renderizar siempre el formulario, incluso si hay errores
    return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')  # <-- sin namespace

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Registrar actividad
            registrar_actividad(
                user,
                'LOGIN',
                f'{user.username} inició sesión',
                request
            )
            
            messages.success(request, f'¡Bienvenido, {user.first_name}!')

            # Redirigir a 'next' si viene en GET, sino al dashboard
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # <-- CORRECCIÓN AQUÍ
            return redirect('dashboard:home')  # ya no 'dashboard:home'

    else:
        form = LoginForm(request)

    return render(request, 'usuarios/login.html', {'form': form})



@login_required
def logout_view(request):
    """Vista de cierre de sesión"""



    registrar_actividad(
        request.user,
        'LOGOUT',
        f'{request.user.username} cerró sesión',
        request
    )

    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('index')


@login_required
@user_passes_test(es_admin)
def editar_usuario_completo_view(request, usuario_id):
    """Editar usuario completo (admin)"""
    usuario_editar = get_object_or_404(Usuario, id=usuario_id)

    # 🔒 VALIDACIÓN ANTES DE TODO (GET Y POST)
    if usuario_editar.rol == 'SUPER_ADMIN' and usuario_editar != request.user:
        messages.error(request, '🔒 No puedes editar al Super Administrador.')
        return redirect('usuarios:gestionar_usuarios')

    if request.method == 'POST':
        # Campos básicos
        usuario_editar.first_name = request.POST.get('first_name', '').strip()
        usuario_editar.last_name = request.POST.get('last_name', '').strip()
        usuario_editar.email = request.POST.get('email', '').strip()
        usuario_editar.telefono = request.POST.get('telefono', '').strip()
        nuevo_documento = request.POST.get('documento', '').strip()

        # Validar documento único
        if Usuario.objects.exclude(id=usuario_editar.id).filter(documento=nuevo_documento).exists():
            messages.error(request, "❌ Ya existe un usuario con ese número de documento.")
            return redirect('usuarios:editar_usuario_completo', usuario_id=usuario_editar.id)

        usuario_editar.documento = nuevo_documento
        usuario_editar.rol = request.POST.get('rol')
        usuario_editar.is_active = request.POST.get('is_active') == 'on'

        if not usuario_editar.aprobado and request.POST.get('aprobado') == 'on':
            usuario_editar.aprobar_usuario(request.user)
            # enviar_email_aprobacion(usuario_editar, request.user)
        else:
            usuario_editar.aprobado = request.POST.get('aprobado') == 'on'

        # Grupos
        grupos_ids = request.POST.getlist('grupos')
        usuario_editar.groups.set(grupos_ids)

        usuario_editar.save()

        registrar_actividad(
            request.user,
            'EDITAR',
            f'Editó el usuario {usuario_editar.username}',
            request
        )

        messages.success(request, f'Usuario {usuario_editar.username} actualizado correctamente.')
        return redirect('usuarios:gestionar_usuarios')

    # GET: mostrar formulario
    grupos_disponibles = Group.objects.all()
    grupos_usuario = list(usuario_editar.groups.values_list('id', flat=True))

    return render(request, 'usuarios/editar_usuario_completo.html', {
        'usuario_editar': usuario_editar,
        'grupos_disponibles': grupos_disponibles,
        'grupos_usuario': grupos_usuario,
    })

# ========== GESTIÓN DE USUARIOS (ADMIN) ==========
@login_required
@user_passes_test(es_admin)
def gestionar_usuarios_view(request):
    """Vista para que administradores gestionen usuarios"""
    filtro = request.GET.get('filtro', 'todos')
    busqueda = request.GET.get('q', '')
    
    usuarios = Usuario.objects.all()
    


    if filtro == 'pendientes':
        usuarios = usuarios.filter(aprobado=False)
    elif filtro == 'aprobados':
        usuarios = usuarios.filter(aprobado=True)
    elif filtro == 'activos':
        usuarios = usuarios.filter(is_active=True)
    elif filtro == 'inactivos':
        usuarios = usuarios.filter(is_active=False)
    



    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda) |
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(email__icontains=busqueda) |
            Q(documento__icontains=busqueda)
        )
    
    usuarios = usuarios.order_by('-date_joined')
    


    stats = {
        'total': Usuario.objects.count(),
        'pendientes': Usuario.objects.filter(aprobado=False).count(),
        'aprobados': Usuario.objects.filter(aprobado=True).count(),
        'activos': Usuario.objects.filter(is_active=True).count(),
    }
    
    context = {
        'usuarios': usuarios,
        'stats': stats,
        'filtro': filtro,
        'busqueda': busqueda
    }
    return render(request, 'usuarios/gestionar_usuarios.html', context)


@login_required
@user_passes_test(es_admin)
def aprobar_usuario_view(request, usuario_id):
    """Vista para aprobar un usuario y asignarle sucursal"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        form = AprobarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            # Validar que si se aprueba, tenga sucursal
            if form.cleaned_data['aprobado'] and not form.cleaned_data['sucursal']:
                messages.error(
                    request,
                    '❌ Debes asignar una sucursal antes de aprobar al usuario.'
                )
                return render(request, 'usuarios/aprobar_usuario.html', {
                    'form': form,
                    'usuario_obj': usuario
                })
            
            usuario = form.save(commit=False)
            
            # Si se está aprobando por primera vez
            if usuario.aprobado and not usuario.fecha_aprobacion:
                usuario.fecha_aprobacion = timezone.now()
                usuario.aprobado_por = request.user
            
            usuario.save()
            
            # Enviar email y registrar actividad si fue aprobado
            if usuario.aprobado:
                enviar_email_aprobacion(usuario, request.user)
                
                registrar_actividad(
                    request.user,
                    'EDITAR',
                    f'Aprobó la cuenta de {usuario.username} y lo asignó a {usuario.sucursal.nombre}',
                    request
                )
                
                messages.success(
                    request, 
                    f'✅ Usuario {usuario.username} aprobado y asignado a {usuario.sucursal.nombre}.'
                )
            else:
                registrar_actividad(
                    request.user,
                    'EDITAR',
                    f'Actualizó información de {usuario.username}',
                    request
                )
                messages.info(request, f'Usuario {usuario.username} actualizado.')
            
            return redirect('usuarios:gestionar_usuarios')
    else:
        form = AprobarUsuarioForm(instance=usuario)
    
    context = {
        'form': form,
        'usuario_obj': usuario
    }
    return render(request, 'usuarios/aprobar_usuario.html', context)


@login_required
@user_passes_test(es_admin)
def toggle_usuario_view(request, usuario_id):
    """Activar/desactivar usuario"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    


    if usuario == request.user:
        messages.error(request, '❌ No puedes desactivar tu propia cuenta.')
        return redirect('usuarios:gestionar_usuarios')
    
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    estado = 'activó' if usuario.is_active else 'desactivó'
    
    registrar_actividad(
        request.user,
        'EDITAR',
        f'{estado.capitalize()} la cuenta de {usuario.username}',
        request
    )
    
    messages.success(
        request, 
        f'✅ Usuario {usuario.username} {estado} correctamente.'
    )
    
    return redirect('usuarios:gestionar_usuarios')


@login_required
@user_passes_test(es_admin)
def gestionar_grupos_view(request):
    """Vista para gestionar grupos de usuarios"""
    grupos = Group.objects.all().prefetch_related('permissions')
    
    context = {
        'grupos': grupos
    }
    return render(request, 'usuarios/gestionar_grupos.html', context)


@login_required
@user_passes_test(es_admin)
def crear_grupo_view(request):
    """Crear nuevo grupo"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        permisos_ids = request.POST.getlist('permisos')
        
        if nombre:
            grupo = Group.objects.create(name=nombre)
            grupo.permissions.set(permisos_ids)
            grupo.save()
            
            registrar_actividad(
                request.user,
                'CREAR',
                f'Creó el grupo: {nombre}',
                request
            )
            
            messages.success(request, f'Grupo "{nombre}" creado correctamente.')
            return redirect('usuarios:gestionar_grupos')
    
    # Obtener todos los permisos disponibles organizados por modelo
    permisos = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'content_type__model')
    
    # Organizar permisos por app y modelo
    permisos_organizados = {}
    for permiso in permisos:
        app = permiso.content_type.app_label
        modelo = permiso.content_type.model
        
        if app not in permisos_organizados:
            permisos_organizados[app] = {}
        
        if modelo not in permisos_organizados[app]:
            permisos_organizados[app][modelo] = []
        
        permisos_organizados[app][modelo].append(permiso)
    
    context = {
        'permisos_organizados': permisos_organizados
    }
    return render(request, 'usuarios/crear_grupo.html', context)


@login_required
@user_passes_test(es_admin)
def editar_grupo_view(request, grupo_id):
    """Editar grupo existente"""
    grupo = get_object_or_404(Group, id=grupo_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        permisos_ids = request.POST.getlist('permisos')
        
        grupo.name = nombre
        grupo.permissions.set(permisos_ids)
        grupo.save()
        
        registrar_actividad(
            request.user,
            'EDITAR',
            f'Editó el grupo: {nombre}',
            request
        )
        
        messages.success(request, f'Grupo "{nombre}" actualizado.')
        return redirect('usuarios:gestionar_grupos')
    
    # Obtener permisos organizados
    permisos = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'content_type__model')
    
    permisos_organizados = {}
    for permiso in permisos:
        app = permiso.content_type.app_label
        modelo = permiso.content_type.model
        
        if app not in permisos_organizados:
            permisos_organizados[app] = {}
        
        if modelo not in permisos_organizados[app]:
            permisos_organizados[app][modelo] = []
        
        permisos_organizados[app][modelo].append(permiso)
    
    context = {
        'grupo': grupo,
        'permisos_organizados': permisos_organizados,
        'permisos_grupo': list(grupo.permissions.values_list('id', flat=True))
    }
    return render(request, 'usuarios/editar_grupo.html', context)


@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_grupo_view(request, grupo_id):
    """Eliminar grupo"""
    grupo = get_object_or_404(Group, id=grupo_id)
    nombre = grupo.name
    grupo.delete()
    
    registrar_actividad(
        request.user,
        'ELIMINAR',
        f'Eliminó el grupo: {nombre}',
        request
    )
    
    messages.success(request, f'Grupo "{nombre}" eliminado.')
    return redirect('usuarios:gestionar_grupos')




@login_required
@user_passes_test(es_admin)
def resetear_password_view(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        nueva_password = request.POST.get('nueva_password', '').strip()
        if nueva_password:
            usuario.set_password(nueva_password)
            usuario.save()

            registrar_actividad(
                request.user,
                'EDITAR',
                f'Reseteó la contraseña de {usuario.username}',
                request
            )

            messages.success(request, f'Contraseña de {usuario.username} reseteada.')
            return redirect('usuarios:gestionar_usuarios')

    return render(request, 'usuarios/resetear_password.html', {
        'usuario': usuario
    })


@login_required
@user_passes_test(es_admin)
def eliminar_usuario_view(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('usuarios:gestionar_usuarios')

    if request.method == 'POST':
        usuario.is_active = False
        usuario.save()

        registrar_actividad(
            request.user,
            'ELIMINAR',
            f'Desactivó al usuario {usuario.username}',
            request
        )

        messages.success(request, f'Usuario {usuario.username} desactivado.')
        return redirect('usuarios:gestionar_usuarios')

    return render(request, 'usuarios/eliminar_usuario.html', {
        'usuario': usuario
    })



@login_required




@user_passes_test(es_admin)
def detalle_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)

    productos = Producto.objects.filter(creado_por=usuario)
    productos_activos = productos.filter(activo=True)
    productos_inactivos = productos.filter(activo=False)

    context = {
        "usuario_detalle": usuario,
        "productos": productos,
        "productos_activos": productos_activos,
        "productos_inactivos": productos_inactivos,
    }

    return render(request, "usuarios/detalle_usuario.html", context)


# ========== PANEL DE ELIMINADOS ==========
@login_required
@user_passes_test(es_admin)
def panel_eliminados_view(request):
    """Página central para que los admins vean items eliminados (soft-deleted)"""
    productos_inactivos = Producto.objects.filter(activo=False).order_by('-fecha_creacion')
    productos_activos = Producto.objects.filter(activo=True).order_by('-fecha_creacion')[:8]

    categorias_inactivas = Categoria.objects.filter(activa=False).order_by('-fecha_creacion')
    categorias_activas = Categoria.objects.filter(activa=True).order_by('nombre')[:8]

    proveedores_inactivos = Proveedor.objects.filter(activo=False).order_by('-fecha_registro')
    proveedores_activos = Proveedor.objects.filter(activo=True).order_by('nombre')[:8]

    usuarios_inactivos = Usuario.objects.filter(is_active=False).order_by('-date_joined')
    usuarios_activos = Usuario.objects.filter(is_active=True).order_by('-date_joined')[:8]

    context = {
        'productos_inactivos': productos_inactivos,
        'productos_activos_preview': productos_activos,
        'categorias_inactivas': categorias_inactivas,
        'categorias_activas_preview': categorias_activas,
        'proveedores_inactivos': proveedores_inactivos,
        'proveedores_activos_preview': proveedores_activos,
        'usuarios_inactivos': usuarios_inactivos,
        'usuarios_activos_preview': usuarios_activos,
    }
    return render(request, 'usuarios/panel_eliminados.html', context)


# ========== RESTAURAR ==========
@login_required
@user_passes_test(es_admin)
@require_POST
def restaurar_producto(request, producto_id):
    p = get_object_or_404(Producto, id=producto_id)
    p.activo = True
    p.save()
    messages.success(request, f'Producto "{p.nombre}" restaurado.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados'))

@login_required
@user_passes_test(es_admin)
@require_POST
def restaurar_categoria(request, categoria_id):
    c = get_object_or_404(Categoria, id=categoria_id)
    c.activa = True
    c.save()
    messages.success(request, f'Categoría "{c.nombre}" restaurada.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados'))

@login_required
@user_passes_test(es_admin)
@require_POST
def restaurar_proveedor(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    prov.activo = True
    prov.save()
    messages.success(request, f'Proveedor "{prov.nombre}" restaurado.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados'))

@login_required
@user_passes_test(es_admin)
@require_POST
def restaurar_usuario(request, usuario_id):
    u = get_object_or_404(Usuario, id=usuario_id)
    u.is_active = True
    u.save()
    messages.success(request, f'Usuario "{u.username}" restaurado (reactivado).')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados'))


# ========== ELIMINAR DEFINITIVO ==========
@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_producto_definitivo(request, producto_id):
    p = get_object_or_404(Producto, id=producto_id)
    nombre = str(p)
    p.delete()
    messages.success(request, f'Producto "{nombre}" eliminado permanentemente.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados'))

@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_categoria_definitivo(request, categoria_id):
    c = get_object_or_404(Categoria, id=categoria_id)
    nombre = str(c)

    try:
        c.delete()
        messages.success(
            request,
            f'🗑️ Categoría "{nombre}" eliminada permanentemente.'
        )
    except ProtectedError:
        messages.error(
            request,
            f'⚠️ No se puede eliminar la categoría "{nombre}" '
            'porque tiene productos asociados.'
        )

    return redirect(
        request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados')
    )

@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_proveedor_definitivo(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    nombre = str(prov)
    prov.delete()
    messages.success(request, f'Proveedor "{nombre}" eliminado permanentemente.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados'))

@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_usuario_definitivo(request, usuario_id):
    u = get_object_or_404(Usuario, id=usuario_id)
    nombre = str(u)
    u.delete()
    messages.success(request, f'Usuario "{nombre}" eliminado permanentemente.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:panel_eliminados'))


# ========== DESACTIVAR (SOFT DELETE) ==========
@login_required
@user_passes_test(es_admin)
@require_POST
def desactivar_producto(request, producto_id):
    """Soft delete: marca producto como inactivo"""
    p = get_object_or_404(Producto, id=producto_id)
    p.activo = False
    p.save()
    
    registrar_actividad(
        request.user,
        'ELIMINAR',
        f'Desactivó el producto: {p.nombre} ({p.codigo})',
        request
    )
    
    messages.warning(request, f'Producto "{p.nombre}" movido a papelera.')
    return redirect(request.META.get('HTTP_REFERER', 'inventario:lista_productos'))


@login_required
@user_passes_test(es_admin)
@require_POST
def desactivar_categoria(request, categoria_id):
    """Soft delete: marca categoría como inactiva"""
    c = get_object_or_404(Categoria, id=categoria_id)
    
    productos_asociados = Producto.objects.filter(categoria=c, activo=True).count()
    if productos_asociados > 0:
        messages.error(request, f'No se puede eliminar. La categoría "{c.nombre}" tiene {productos_asociados} productos activos.')
        return redirect(request.META.get('HTTP_REFERER', 'categorias:lista'))
    
    c.activa = False
    c.save()
    
    registrar_actividad(
        request.user,
        'ELIMINAR',
        f'Desactivó la categoría: {c.nombre}',
        request
    )
    
    messages.warning(request, f'Categoría "{c.nombre}" movida a papelera.')
    return redirect(request.META.get('HTTP_REFERER', 'categorias:lista'))


@login_required
@user_passes_test(es_admin)
@require_POST
def desactivar_proveedor(request, proveedor_id):
    """Soft delete: marca proveedor como inactivo"""
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    prov.activo = False
    prov.save()
    
    registrar_actividad(
        request.user,
        'ELIMINAR',
        f'Desactivó el proveedor: {prov.nombre} (NIT: {prov.nit})',
        request
    )
    
    messages.warning(request, f'Proveedor "{prov.nombre}" movido a papelera.')
    return redirect(request.META.get('HTTP_REFERER', 'proveedores:lista'))


@login_required
@user_passes_test(es_admin)
@require_POST
def desactivar_usuario(request, usuario_id):
    """Soft delete: marca usuario como inactivo"""
    u = get_object_or_404(Usuario, id=usuario_id)
    
    if u == request.user:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
        return redirect(request.META.get('HTTP_REFERER', 'usuarios:gestionar_usuarios'))
    
    if u.rol == 'SUPER_ADMIN':
        super_admins_activos = Usuario.objects.filter(rol='SUPER_ADMIN', is_active=True).count()
        if super_admins_activos <= 1:
            messages.error(request, 'No se puede desactivar el último Super Administrador.')
            return redirect(request.META.get('HTTP_REFERER', 'usuarios:gestionar_usuarios'))
    
    u.is_active = False
    u.save()
    
    registrar_actividad(
        request.user,
        'ELIMINAR',
        f'Desactivó al usuario: {u.username} ({u.get_full_name()})',
        request
    )
    
    messages.warning(request, f'Usuario "{u.username}" desactivado.')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:gestionar_usuarios'))



@login_required
def perfil_view(request):
    """Vista del perfil del usuario"""
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            registrar_actividad(request.user, 'EDITAR', 'Usuario actualizó su perfil', request)
            messages.success(request, '✅ Perfil actualizado correctamente.')
            return redirect('usuarios:perfil')
    else:
        form = PerfilUsuarioForm(instance=request.user)

    actividades = HistorialActividad.objects.filter(usuario=request.user).order_by('-fecha')[:10]

    context = {
        'form': form,
        'actividades': actividades
    }
    return render(request, 'usuarios/perfil.html', context)


@login_required
def cambiar_password_view(request):
    """Vista para cambiar contraseña"""
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            # Enviar correo notificando el cambio
            send_mail(
                'Cambio de contraseña en SISBAR',
                f'Hola {user.username},\n\nTu contraseña fue cambiada correctamente.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            registrar_actividad(
                request.user,
                'EDITAR',
                'Usuario cambió su contraseña',
                request
            )

            messages.success(request, '✅ Contraseña cambiada exitosamente.')
            return redirect('usuarios:perfil')
    else:
        form = CambiarPasswordForm(request.user)

    return render(request, 'usuarios/cambiar_password.html', {'form': form})
@login_required
@user_passes_test(es_admin)
def asignar_sucursal_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    sucursales = Sucursal.objects.all()

    if request.method == 'POST':
        sucursal_id = request.POST.get('sucursal')
        if sucursal_id:
            sucursal = get_object_or_404(Sucursal, id=sucursal_id)
            usuario.sucursal = sucursal
            usuario.save()
            messages.success(request, f'Sucursal {sucursal.nombre} asignada a {usuario.username}')
            return redirect('usuarios:gestionar_usuarios')

    return render(request, 'usuarios/asignar_sucursal.html', {
        'usuario': usuario,
        'sucursales': sucursales
    })

@login_required
def dashboard_view(request):
    """Vista del dashboard principal"""
    # Aquí puedes enviar al template los datos que quieras mostrar
    total_usuarios = Usuario.objects.count()
    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    total_proveedores = Proveedor.objects.count()

    context = {
        'total_usuarios': total_usuarios,
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'total_proveedores': total_proveedores,
    }

    return render(request, 'usuarios/dashboard.html', context)

