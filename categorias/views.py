from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Categoria, Subcategoria
from usuarios.views import registrar_actividad
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect


@login_required
def listar_categorias_view(request):
    """Lista todas las categorías con sus subcategorías"""
    categorias = Categoria.objects.filter(activa=True).prefetch_related('subcategorias')
    
    context = {
        'categorias': categorias,
    }
    return render(request, 'categorias/listar.html', context)


@login_required
def crear_categoria_view(request):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para crear categoria")
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre').strip()
        icono = request.POST.get('icono', '📦')
        color = request.POST.get('color', '#3B82F6')
        descripcion = request.POST.get('descripcion', '')

        # Verificar si YA existe
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'❌ La categoría "{nombre}" ya existe.')
            return redirect('categorias:crear')

        # Crear categoría
        Categoria.objects.create(
            nombre=nombre,
            icono=icono,
            color=color,
            descripcion=descripcion
        )

        registrar_actividad(
            request.user,
            'CREAR',
            f'Creó la categoría {nombre}',
            request
        )

        messages.success(request, f'✅ Categoría {nombre} creada exitosamente.')
        return redirect('categorias:listar')

    return render(request, 'categorias/crear.html')

@login_required
def crear_subcategoria_view(request, categoria_id):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para crear sudcategorias")
    
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        
        if nombre:
            Subcategoria.objects.create(
                categoria=categoria,
                nombre=nombre,
                descripcion=descripcion
            )
            
            registrar_actividad(
                request.user,
                'CREAR',
                f'Creó la subcategoría {nombre} en {categoria.nombre}',
                request
            )
            
            messages.success(request, f'✅ Subcategoría {nombre} creada.')
            return redirect('categorias:listar')
    
    context = {'categoria': categoria}
    return render(request, 'categorias/crear_subcategoria.html', context)


@login_required
def editar_categoria_view(request, categoria_id):
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para editar categoria")
    
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    if request.method == 'POST':
        categoria.nombre = request.POST.get('nombre')
        categoria.icono = request.POST.get('icono')
        categoria.color = request.POST.get('color')
        categoria.descripcion = request.POST.get('descripcion', '')
        categoria.save()
        
        registrar_actividad(
            request.user,
            'EDITAR',
            f'Editó la categoría {categoria.nombre}',
            request
        )
        
        messages.success(request, f'✅ Categoría actualizada.')
        return redirect('categorias:listar')
    
    context = {'categoria': categoria}
    return render(request, 'categorias/editar.html', context)


@login_required
def eliminar_categoria_view(request, categoria_id):
    """Desactivar categoría"""
        # 🔒 BLOQUEO REAL POR ROL
    if request.user.rol not in ['SUPER_ADMIN', 'ADMIN']:
        return HttpResponseForbidden("No tienes permisos para eliminar categoria")
    
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    if request.method == 'POST':
        categoria.activa = False
        categoria.save()
        
        registrar_actividad(
            request.user,
            'ELIMINAR',
            f'Desactivó la categoría {categoria.nombre}',
            request
        )
        
        messages.success(request, f'✅ Categoría desactivada.')
        return redirect('categorias:listar')
    
    context = {'categoria': categoria}
    return render(request, 'categorias/eliminar.html', context)