from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

from inventario.models import Producto, InventarioSucursal
from proveedores.models import Proveedor
from sucursales.models import Sucursal
from usuarios.models import Usuario


class SugerenciaCompra(models.Model):
    """
    Sugerencias inteligentes de compra generadas por IA
    """
    
    URGENCIAS = (
        ('URGENTE', '🔴 URGENTE - Stock crítico'),
        ('ALTA', '🟠 ALTA - Stock bajo'),
        ('MEDIA', '🟡 MEDIA - Planificar'),
        ('BAJA', '🟢 BAJA - Stock suficiente'),
    )
    
    #clase_abc = models.CharField(
    #max_length=1,
    #choices=Producto.CLASES_ABC,
    #default='C'
    #)
    
    # Producto y sucursal
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='sugerencias_compra',
        verbose_name='Producto'
    )
    
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sugerencias_compra',
        verbose_name='Sucursal'
    )
    
    # Datos de inventario actual
    stock_actual = models.IntegerField(
        default=0,
        verbose_name='Stock Actual'
    )
    
    stock_minimo = models.IntegerField(
        default=0,
        verbose_name='Stock Mínimo Configurado'
    )
    
    # Análisis de ventas
    promedio_ventas_diarias = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Promedio Ventas Diarias'
    )
    
    dias_stock_restante = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Días de Stock Restante'
    )
    
    # Predicción IA
    prediccion_proximos_30_dias = models.IntegerField(
        default=0,
        verbose_name='Predicción Ventas 30 Días (IA)',
        help_text='Calculado con Prophet'
    )
    
    tendencia = models.CharField(
        max_length=20,
        choices=(
            ('CRECIENTE', '📈 Ventas Aumentando'),
            ('ESTABLE', '➡️ Ventas Estables'),
            ('DECRECIENTE', '📉 Ventas Disminuyendo'),
        ),
        default='ESTABLE',
        verbose_name='Tendencia de Ventas'
    )
    
    # Sugerencia
    cantidad_sugerida = models.IntegerField(
        default=0,
        verbose_name='Cantidad Sugerida a Comprar'
    )
    
    punto_reorden = models.IntegerField(
        default=0,
        verbose_name='Punto de Reorden',
        help_text='Stock en el que se debe pedir'
    )
    
    dias_cobertura_deseada = models.IntegerField(
        default=30,
        verbose_name='Días de Cobertura Deseada'
    )
    
    # Urgencia
    urgencia = models.CharField(
        max_length=20,
        choices=URGENCIAS,
        default='MEDIA',
        verbose_name='Nivel de Urgencia'
    )
    
    # Costos
    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Costo Unitario'
    )
    
    inversion_estimada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Inversión Estimada Total'
    )
    
    # Proveedor sugerido
    proveedor_sugerido = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sugerencias',
        verbose_name='Proveedor Sugerido'
    )
    
    # Metadatos
    fecha_generacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Generación'
    )
    
    generado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sugerencias_generadas',
        verbose_name='Generado Por'
    )
    
    razon = models.TextField(
        blank=True,
        verbose_name='Razón de la Sugerencia'
    )
    
    confianza_ia = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Confianza del Modelo IA (%)'
    )
    
    class Meta:
        verbose_name = 'Sugerencia de Compra'
        verbose_name_plural = 'Sugerencias de Compra'
        ordering = ['urgencia', '-dias_stock_restante']
        indexes = [
            models.Index(fields=['urgencia', 'fecha_generacion']),
            models.Index(fields=['sucursal', 'urgencia']),
        ]
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.get_urgencia_display()} - {self.cantidad_sugerida} unidades"
    
    def save(self, *args, **kwargs):
        # Calcular inversión estimada
        self.inversion_estimada = self.cantidad_sugerida * self.costo_unitario
        super().save(*args, **kwargs)


class ConfiguracionCompras(models.Model):
    """
    Configuración global del módulo de compras
    """
    dias_cobertura_default = models.IntegerField(
        default=30,
        verbose_name='Días de Cobertura por Defecto',
        help_text='Stock para cuántos días mantener'
    )
    
    stock_seguridad_porcentaje = models.IntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Stock de Seguridad (%)',
        help_text='Porcentaje adicional de seguridad'
    )
    
    dias_analisis_historico = models.IntegerField(
        default=90,
        validators=[MinValueValidator(7), MaxValueValidator(365)],
        verbose_name='Días de Histórico para Análisis',
        help_text='Cuántos días atrás analizar ventas'
    )
    
    umbral_urgente_dias = models.IntegerField(
        default=3,
        verbose_name='Umbral URGENTE (días)',
        help_text='Stock para menos de X días = URGENTE'
    )
    
    umbral_alta_dias = models.IntegerField(
        default=7,
        verbose_name='Umbral ALTA (días)',
        help_text='Stock para menos de X días = ALTA'
    )
    
    umbral_media_dias = models.IntegerField(
        default=15,
        verbose_name='Umbral MEDIA (días)',
        help_text='Stock para menos de X días = MEDIA'
    )
    
    habilitar_ia = models.BooleanField(
        default=True,
        verbose_name='Habilitar Predicción con IA',
        help_text='Usar Prophet para predicciones'
    )
    
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Configuración de Compras'
        verbose_name_plural = 'Configuraciones de Compras'
    
    def __str__(self):
        return f"Configuración ({self.dias_cobertura_default} días cobertura)"
    

class CachePrediccion(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    prediccion = models.IntegerField()
    confianza = models.DecimalField(max_digits=5, decimal_places=2)
    tendencia = models.CharField(max_length=20)

    fecha_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['producto', 'sucursal']

    def __str__(self):
        return f"Cache IA {self.producto}"