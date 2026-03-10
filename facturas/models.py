from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class Cliente(models.Model):
    """
    Información de clientes para facturación
    """
    TIPO_DOCUMENTO = (
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('NIT', 'NIT'),
        ('TI', 'Tarjeta de Identidad'),
        ('PP', 'Pasaporte'),
        ('RC', 'Registro Civil'),
    )
    
    tipo_documento = models.CharField(
        max_length=3,
        choices=TIPO_DOCUMENTO,
        default='CC',
        verbose_name='Tipo de Documento'
    )
    
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de Documento'
    )
    
    nombre_completo = models.CharField(
        max_length=200,
        verbose_name='Nombre Completo / Razón Social'
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='Correo Electrónico'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
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
    
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Cliente Activo'
    )
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre_completo']
        db_table = 'inventario_cliente'  # ✅ Mantener nombre de tabla original
    
    def __str__(self):
        return f"{self.nombre_completo} ({self.numero_documento})"


class Factura(models.Model):
    """
    Factura de venta legal completa
    """
    METODOS_PAGO = (
        ('EFECTIVO', '💵 Efectivo'),
        ('TARJETA_DEBITO', '💳 Tarjeta Débito'),
        ('TARJETA_CREDITO', '💳 Tarjeta Crédito'),
        ('TRANSFERENCIA', '🏦 Transferencia Bancaria'),
        ('NEQUI', '📱 Nequi'),
        ('DAVIPLATA', '📱 Daviplata'),
        ('CREDITO', '📋 Crédito'),
        ('OTRO', '🔄 Otro'),
    )
    
    numero_factura = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Factura'
    )
    
    prefijo = models.CharField(
        max_length=10,
        default='FAC',
        verbose_name='Prefijo'
    )
    
    consecutivo = models.IntegerField(
        verbose_name='Consecutivo'
    )
    
    sucursal = models.ForeignKey(
        'sucursales.Sucursal',
        on_delete=models.CASCADE,
        related_name='facturas',
        verbose_name='Sucursal'
    )
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='facturas',
        verbose_name='Cliente'
    )
    
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='facturas',
        verbose_name='Vendedor'
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Subtotal (sin impuestos)'
    )
    
    impuesto_consumo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Impuesto al Consumo (8%)'
    )
    
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Descuento'
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total a Pagar'
    )
    
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        default='EFECTIVO',
        verbose_name='Método de Pago'
    )
    
    monto_recibido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Monto Recibido'
    )
    
    cambio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Cambio'
    )
    
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Emisión'
    )
    
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento',
        help_text='Solo para ventas a crédito'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    enviada_por_email = models.BooleanField(
        default=False,
        verbose_name='Enviada por Email'
    )
    
    fecha_envio_email = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Envío Email'
    )
    
    anulada = models.BooleanField(
        default=False,
        verbose_name='Factura Anulada'
    )
    
    motivo_anulacion = models.TextField(
        blank=True,
        verbose_name='Motivo de Anulación'
    )
    
    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha']
        db_table = 'inventario_factura'  # ✅ Mantener nombre de tabla original
        indexes = [
            models.Index(fields=['-fecha']),
            models.Index(fields=['numero_factura']),
        ]
    
    def __str__(self):
        cliente_nombre = self.cliente.nombre_completo if self.cliente else 'Cliente General'
        return f"{self.numero_factura} - {cliente_nombre} - ${self.total}"
    
    def save(self, *args, **kwargs):
        if not self.numero_factura:
            self.numero_factura = self.sucursal.obtener_siguiente_numero_factura()
            partes = self.numero_factura.split('-')
            self.prefijo = partes[0]
            self.consecutivo = int(partes[1])
        
        self.total = self.subtotal + self.impuesto_consumo - self.descuento
        
        if self.metodo_pago == 'EFECTIVO' and self.monto_recibido > 0:
            self.cambio = self.monto_recibido - self.total
        
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        """Recalcula todos los totales basándose en los detalles"""
        detalles = self.detalles.all()
        self.subtotal = sum(d.subtotal for d in detalles)
        
        if self.sucursal.aplica_impuesto_consumo:
            self.impuesto_consumo = self.subtotal * (self.sucursal.porcentaje_impuesto / 100)
        
        self.total = self.subtotal + self.impuesto_consumo - self.descuento
        self.save()


class DetalleFactura(models.Model):
    """
    Detalle de productos en una factura
    """
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Factura'
    )
    
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.CASCADE,
        verbose_name='Producto'
    )
    
    cantidad = models.IntegerField(
        verbose_name='Cantidad'
    )
    
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio Unitario'
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Subtotal'
    )
    
    class Meta:
        verbose_name = 'Detalle de Factura'
        verbose_name_plural = 'Detalles de Factura'
        db_table = 'inventario_detallefactura'  # ✅ Mantener nombre de tabla original
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"