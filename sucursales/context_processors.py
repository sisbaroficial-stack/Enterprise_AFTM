from .models import Sucursal

def sucursal_actual(request):
    """
    Hace disponible la sucursal actual en todos los templates
    """
    sucursal = None
    if request.user.is_authenticated:
        sucursal_id = request.session.get('sucursal_actual')
        if sucursal_id:
            try:
                sucursal = Sucursal.objects.get(id=sucursal_id)
            except Sucursal.DoesNotExist:
                pass
    
    return {
        'sucursal_actual': sucursal
    }