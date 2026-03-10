from django.db import models
from usuarios.models import Usuario
from django.db import models, transaction # Importante agregar transaction
class Sucursal(models.Model):
    """
    Modelo para las diferentes tiendas/sucursales
    """
    TIPOS = (
        ('BODEGA', '🏭 Bodega Principal'),
        ('TIENDA', '🏪 Tienda'),
        ('PUNTO_VENTA', '🛒 Punto de Venta'),
    )
    
    # ============ INFORMACIÓN BÁSICA ============
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
    
    # ============ DATOS LEGALES (PARA FACTURACIÓN) ============
    razon_social = models.CharField(
        max_length=200,
        default='AFTM SAS',
        verbose_name='Razón Social'
    )
    
    nit = models.CharField(
        max_length=20,
        default='000000-0',
        verbose_name='NIT',
        help_text='Número de Identificación Tributaria'
    )
    
    regimen = models.CharField(
        max_length=50,
        default='Responsable de IVA - Régimen Común',
        verbose_name='Régimen Tributario'
    )
    
    # ============ RESOLUCIÓN DIAN ============
    resolucion_dian = models.CharField(
        max_length=50,
        default='RES-DIAN-2024-001',
        verbose_name='Resolución DIAN',
        help_text='Número de resolución de facturación'
    )
    
    fecha_resolucion = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Resolución'
    )
    
    prefijo_factura = models.CharField(
        max_length=10,
        default='FAC',
        verbose_name='Prefijo de Factura',
        help_text='Ej: FAC, FV, INV'
    )
    
    rango_desde = models.IntegerField(
        default=1,
        verbose_name='Rango Desde',
        help_text='Número inicial autorizado'
    )
    
    rango_hasta = models.IntegerField(
        default=19445578,
        verbose_name='Rango Hasta',
        help_text='Número final autorizado'
    )
    
    consecutivo_actual = models.IntegerField(
        default=1,
        verbose_name='Consecutivo Actual',
        help_text='Próximo número de factura'
    )
    
    # ============ INFORMACIÓN DE CONTACTO ============
    email_facturacion = models.EmailField(
        default='sisbaroficial@gmail.com',
        verbose_name='Email para Facturación'
    )
    
    sitio_web = models.URLField(
        blank=True,
        verbose_name='Sitio Web'
    )
    
    # ============ CONFIGURACIÓN ============
    activa = models.BooleanField(
        default=True,
        verbose_name='Sucursal Activa'
    )
    
    es_principal = models.BooleanField(
        default=False,
        verbose_name='Es Bodega Principal',
        help_text='Solo puede haber una bodega principal'
    )
    
    # ============ IMPUESTOS ============
    aplica_impuesto_consumo = models.BooleanField(
        default=False,
        verbose_name='Aplica Impuesto al Consumo',
        help_text='Si aplica impuesto del 8% a ciertos productos'
    )
    
    porcentaje_impuesto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=8.00,
        verbose_name='% Impuesto al Consumo'
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
    
    def obtener_siguiente_numero_factura(self):
        """
        Obtiene el consecutivo bloqueando la fila para evitar que 
        dos vendedores tomen el mismo número al mismo tiempo.
        """
        from facturas.models import Factura 
        
        # Usamos un bloque atómico para asegurar que el 'candado' funcione
        with transaction.atomic():
            # select_for_update() pone el candado a esta sucursal específica
            sucursal = Sucursal.objects.select_for_update().get(pk=self.pk)
            
            numero = sucursal.consecutivo_actual
            prefijo = sucursal.prefijo_factura
            
            # Doble chequeo de seguridad por si acaso
            while Factura.objects.filter(numero_factura=f"{prefijo}-{str(numero).zfill(8)}").exists():
                numero += 1
                
            # Actualizamos el contador mientras tenemos el candado
            sucursal.consecutivo_actual = numero + 1
            sucursal.save(update_fields=['consecutivo_actual'])
            
            # Al salir del 'with', el candado se libera automáticamente
            return f"{prefijo}-{str(numero).zfill(8)}"
