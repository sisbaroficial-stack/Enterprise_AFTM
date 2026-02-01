from django.db import models
from django.core.validators import MinValueValidator
from inventario.models import Producto
from usuarios.models import Usuario

class Movimiento(models.Model):
    """
    Registro de todos los movimientos de inventario (entradas y salidas)
    """
    
    TIPOS = (
        ('ENTRADA', '📥 Entrada'),
        ('SALIDA', '📤 Salida'),
        ('AJUSTE', '⚖️ Ajuste'),
        ('DEVOLUCION', '↩️ Devolución'),
    )
    
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='movimientos_antiguos',
        verbose_name='Producto'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        verbose_name='Tipo de Movimiento'
    )
    
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    
    cantidad_anterior = models.IntegerField(
        default=0,
        verbose_name='Cantidad Anterior'
    )
    
    cantidad_nueva = models.IntegerField(
        default=0,
        verbose_name='Cantidad Nueva'
    )
    
    motivo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Motivo',
        help_text='Razón del movimiento'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='movimientos',
        verbose_name='Usuario que Realizó el Movimiento'
    )
    
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y Hora'
    )
    
    class Meta:
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['-fecha']),
            models.Index(fields=['producto', '-fecha']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} - {self.cantidad} ({self.fecha})"
    
    def get_tipo_icono(self):
        """Retorna el icono según el tipo"""
        iconos = {
            'ENTRADA': '📥',
            'SALIDA': '📤',
            'AJUSTE': '⚖️',
            'DEVOLUCION': '↩️'
        }
        return iconos.get(self.tipo, '📦')


class AlertaInventario(models.Model):
    """
    Alertas automáticas de inventario
    """
    
    TIPOS_ALERTA = (
        ('AGOTADO', '🔴 Producto Agotado'),
        ('POR_AGOTAR', '🟡 Producto Por Agotarse'),
        ('REABASTECIMIENTO', '📦 Necesita Reabastecimiento'),
    )
    
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='alertas',
        verbose_name='Producto'
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPOS_ALERTA,
        verbose_name='Tipo de Alerta'
    )
    
    mensaje = models.TextField(
        verbose_name='Mensaje de Alerta'
    )
    
    fecha_generada = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha Generada'
    )
    
    leida = models.BooleanField(
        default=False,
        verbose_name='Alerta Leída'
    )
    
    fecha_lectura = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Lectura'
    )
    
    resuelta = models.BooleanField(
        default=False,
        verbose_name='Alerta Resuelta'
    )
    
    class Meta:
        verbose_name = 'Alerta de Inventario'
        verbose_name_plural = 'Alertas de Inventario'
        ordering = ['-fecha_generada']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre}"
    
    @staticmethod
    def generar_alertas():
        """
        Genera alertas automáticas para productos agotados o por agotarse
        """
        from django.utils import timezone
        
        # Productos agotados
        productos_agotados = Producto.objects.filter(
            cantidad=0,
            activo=True
        )
        
        for producto in productos_agotados:
            # Verificar si ya existe una alerta no resuelta
            existe = AlertaInventario.objects.filter(
                producto=producto,
                tipo='AGOTADO',
                resuelta=False
            ).exists()
            
            if not existe:
                AlertaInventario.objects.create(
                    producto=producto,
                    tipo='AGOTADO',
                    mensaje=f"El producto {producto.nombre} se ha agotado completamente."
                )
        
        # Productos por agotarse
        productos_por_agotar = Producto.objects.filter(
            cantidad__lte=models.F('cantidad_minima'),
            cantidad__gt=0,
            activo=True
        )
        
        for producto in productos_por_agotar:
            existe = AlertaInventario.objects.filter(
                producto=producto,
                tipo='POR_AGOTAR',
                resuelta=False
            ).exists()
            
            if not existe:
                AlertaInventario.objects.create(
                    producto=producto,
                    tipo='POR_AGOTAR',
                    mensaje=f"El producto {producto.nombre} está por agotarse. Stock actual: {producto.cantidad}"
                )