from django.shortcuts import redirect
from django.urls import reverse
from sucursales.models import Sucursal

class SucursalMiddleware:
    """
    Middleware para verificar que el usuario tenga una sucursal seleccionada
    """
    EXCLUDED_URLS = [
        '/sucursales/seleccionar/',
        '/sucursales/establecer/',
        '/sucursales/crear/',
        '/usuarios/login/',
        '/usuarios/logout/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        should_check = True
        for url in self.EXCLUDED_URLS:
            if request.path.startswith(url):
                should_check = False
                break
        
        if should_check and request.user.is_authenticated:
            # SUPER_ADMIN puede trabajar sin sucursal
            if request.user.rol == 'SUPER_ADMIN':
                return self.get_response(request)
            
            # Usuarios normales necesitan sucursal asignada o en sesión
            if not hasattr(request.user, 'sucursal') or not request.user.sucursal:
                if not request.session.get('sucursal_actual'):
                    return redirect('sucursales:seleccionar')
        
        return self.get_response(request)