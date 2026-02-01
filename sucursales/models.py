from django.db import models
from usuarios.models import Usuario

class Sucursal(models.Model):
    """
    Modelo para las diferentes tiendas/sucursales
    """
    TIPOS = (
        ('BODEGA', '🏭 Bodega Principal'),
        ('TIENDA', '🏪 Tienda'),
        ('PUNTO_VENTA', '🛒 Punto de Venta'),
    )
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la Sucursal'
    )
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Ej: BOD-001, TDA-A, TDA-B'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default='TIENDA',
        verbose_name='Tipo de Sucursal'
    )
    
    direccion = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    
    encargado = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sucursales_a_cargo',
        verbose_name='Encargado'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Sucursal Activa'
    )
    
    es_principal = models.BooleanField(
        default=False,
        verbose_name='Es Bodega Principal',
        help_text='Solo puede haber una bodega principal'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Si es principal, quitar el flag de otras sucursales
        if self.es_principal:
            Sucursal.objects.filter(es_principal=True).update(es_principal=False)
        super().save(*args, **kwargs)