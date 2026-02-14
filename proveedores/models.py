from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Proveedor(models.Model):
    """
    Modelo de proveedores de productos
    """
    
    CALIFICACIONES = (
        (1, '⭐ Muy Malo'),
        (2, '⭐⭐ Malo'),
        (3, '⭐⭐⭐ Regular'),
        (4, '⭐⭐⭐⭐ Bueno'),
        (5, '⭐⭐⭐⭐⭐ Excelente'),
    )
    
    nombre = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Nombre del Proveedor'
    )
    
    nit = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='NIT / RUT'
    )
    
    contacto = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Persona de Contacto'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='Correo Electrónico'
    )
    
    direccion = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )
    
    ciudad = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ciudad'
    )
    
    pais = models.CharField(
        max_length=100,
        default='Colombia',
        verbose_name='País'
    )
    
    sitio_web = models.URLField(
        blank=True,
        verbose_name='Sitio Web'
    )
    
    calificacion = models.IntegerField(
        choices=CALIFICACIONES,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Calificación'
    )
    
    notas = models.TextField(
        blank=True,
        verbose_name='Notas / Observaciones'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Proveedor Activo'
    )
    
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )
    
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    dias_entrega = models.IntegerField(
        default=7,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        verbose_name='Días de Entrega',
        help_text='Tiempo que tarda en entregar después del pedido'
    )
    
    cantidad_minima_pedido = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad Mínima de Pedido',
        help_text='Cantidad mínima que acepta por pedido'
    )
    
    descuento_volumen = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Descuento por Volumen (%)',
        help_text='Descuento si se compra en grandes cantidades'
    )
    
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def total_productos(self):
        """Retorna el total de productos de este proveedor"""
        return self.productos.filter(activo=True).count()
    
    def estrellas(self):
        """Retorna la calificación en estrellas"""
        return '⭐' * self.calificacion