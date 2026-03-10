from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

from categorias.models import Categoria, Subcategoria
from proveedores.models import Proveedor
from sucursales.models import Sucursal

Usuario = get_user_model()


import uuid

class Producto(models.Model):
    """
    Modelo principal de productos en inventario
    """
    
    UNIDADES_MEDIDA = (
        ('UNIDAD', 'Unidad'),
        ('DOCENA', 'Docena'),
        ('CAJA', 'Caja'),
        ('PAQUETE', 'Paquete'),
        ('KILO', 'Kilogramo'),
        ('GRAMO', 'Gramo'),
        ('LITRO', 'Litro'),
        ('METRO', 'Metro'),
        ('PAR', 'Par'),
        ('JUEGO', 'Juego'),
    )
    
    ESTADOS = (
        ('DISPONIBLE', '🟢 Disponible'),
        ('POR_AGOTAR', '🟡 Por Agotarse'),
        ('AGOTADO', '🔴 Agotado'),
    )
    
    # Identificación
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código / Referencia',
        help_text='Código único del producto (puede ser SKU o código de barras)'
    )
    
    codigo_barras = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Código de Barras',
        help_text='Código de barras para escaneo'
    )
    
    # Información básica
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Producto'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    # Categorización
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='Categoría'
    )
    
    subcategoria = models.ForeignKey(
        Subcategoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name='Subcategoría'
    )
    
    # Inventario
    cantidad = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad en Stock'
    )
    
    cantidad_minima = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad Mínima',
        help_text='Alerta cuando llegue a este nivel'
    )
    
    unidad_medida = models.CharField(
        max_length=20,
        choices=UNIDADES_MEDIDA,
        default='UNIDAD',
        verbose_name='Unidad de Medida'
    )
    
    # Precios (solo control interno)
    precio_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de Compra',
        help_text='Precio al que se compra el producto'
    )
        # ✅ AGREGAR ESTOS 3 CAMPOS AQUÍ:
    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de Venta',
        help_text='Precio al que se vende el producto'
    )

    precio_venta_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de Venta Mínimo',
        help_text='No se puede vender por debajo de este precio'
    )

    margen_ganancia = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Margen de Ganancia (%)',
        help_text='Calculado automáticamente'
    )
    aplica_impuesto = models.BooleanField(
    default=False,
    verbose_name='Aplica Impuesto al Consumo (8%)',
    help_text='Marcar si este producto tiene impuesto al consumo'
    )
    # Proveedor
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name='Proveedor'
    )
    
    # Estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='DISPONIBLE',
        verbose_name='Estado del Producto'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Producto Activo',
        help_text='Desactivar en lugar de eliminar'
    )
    
    # Imagen
    imagen = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True,
        verbose_name='Imagen del Producto'
    )
    
    # Ubicación
    ubicacion = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ubicación en Bodega',
        help_text='Estante, pasillo, zona, etc.'
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productos_creados',
        verbose_name='Creado Por'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    ultima_salida = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Salida'
    )
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['codigo_barras']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Actualizar estado automáticamente basado en cantidad
        if self.cantidad == 0:
            self.estado = 'AGOTADO'
        elif self.cantidad <= self.cantidad_minima:
            self.estado = 'POR_AGOTAR'
        else:
            self.estado = 'DISPONIBLE'
        
        # ✅ CALCULAR MARGEN DE GANANCIA AUTOMÁTICAMENTE
        if self.precio_compra > 0 and self.precio_venta > 0:
            self.margen_ganancia = ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        else:
            self.margen_ganancia = 0
        
        # ✅ SI NO HAY PRECIO MÍNIMO, USAR EL PRECIO DE VENTA
        if self.precio_venta_minimo == 0 and self.precio_venta > 0:
            self.precio_venta_minimo = self.precio_venta
        
        super().save(*args, **kwargs)
    
    def descontar_cantidad(self, cantidad, usuario=None):
        """
        Descuenta cantidad del producto
        """
        if cantidad > self.cantidad:
            raise ValueError(f"No hay suficiente stock. Disponible: {self.cantidad}")
        
        self.cantidad -= cantidad
        self.save()
        
        # Registrar el movimiento
        from movimientos.models import Movimiento
        Movimiento.objects.create(
            producto=self,
            tipo='SALIDA',
            cantidad=cantidad,
            usuario=usuario,
            cantidad_anterior=self.cantidad + cantidad,
            cantidad_nueva=self.cantidad
        )
    
    def agregar_cantidad(self, cantidad, usuario=None):
        """
        Agrega cantidad al producto
        """
        cantidad_anterior = self.cantidad
        self.cantidad += cantidad
        self.save()
        
        # Registrar el movimiento
        from movimientos.models import Movimiento
        Movimiento.objects.create(
            producto=self,
            tipo='ENTRADA',
            cantidad=cantidad,
            usuario=usuario,
            cantidad_anterior=cantidad_anterior,
            cantidad_nueva=self.cantidad
        )
    
    def get_estado_color(self):
        """Retorna el color según el estado"""
        colores = {
            'DISPONIBLE': 'success',
            'POR_AGOTAR': 'warning',
            'AGOTADO': 'danger'
        }
        return colores.get(self.estado, 'secondary')
    
    def get_estado_icono(self):
        """Retorna el icono según el estado"""
        iconos = {
            'DISPONIBLE': '🟢',
            'POR_AGOTAR': '🟡',
            'AGOTADO': '🔴'
        }
        return iconos.get(self.estado, '⚪')
    # ✅ AGREGAR ESTA FUNCIÓN AQUÍ:
    def calcular_precio_sugerido(self, margen_deseado=30):
        """Calcula precio de venta sugerido basado en margen deseado"""
        if self.precio_compra > 0:
            return float(self.precio_compra) * (1 + (margen_deseado / 100))
        return 0
    
class InventarioSucursal(models.Model):
    """
    Inventario de productos por sucursal
    """
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.CASCADE,
        related_name='inventarios',
        verbose_name='Producto'
    )
    
    sucursal = models.ForeignKey(
        'sucursales.Sucursal',
        on_delete=models.CASCADE,
        related_name='inventarios',
        verbose_name='Sucursal'
    )
    
    cantidad = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad en Stock'
    )
    
    cantidad_minima = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad Mínima'
    )
    
    ubicacion = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ubicación en Sucursal',
        help_text='Pasillo, estante, etc.'
    )
    
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Inventario por Sucursal'
        verbose_name_plural = 'Inventarios por Sucursal'
        unique_together = ['producto', 'sucursal']
        ordering = ['sucursal', 'producto']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.sucursal.nombre} ({self.cantidad})"
    
    @property
    def estado(self):
        if self.cantidad == 0:
            return 'AGOTADO'
        elif self.cantidad <= self.cantidad_minima:
            return 'POR_AGOTAR'
        return 'DISPONIBLE'


class TransferenciaSucursal(models.Model):
    """
    Transferencias de productos entre sucursales
    """
    ESTADOS = (
        ('PENDIENTE', '⏳ Pendiente'),
        ('EN_TRANSITO', '🚚 En Tránsito'),
        ('RECIBIDA', '✅ Recibida'),
        ('RECHAZADA', '❌ Rechazada'),
    )
    
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código de Transferencia'
    )
    
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.CASCADE,
        related_name='transferencias',
        verbose_name='Producto'
    )
    
    sucursal_origen = models.ForeignKey(
        'sucursales.Sucursal',
        on_delete=models.CASCADE,
        related_name='transferencias_salida',
        verbose_name='Sucursal Origen'
    )
    
    sucursal_destino = models.ForeignKey(
        'sucursales.Sucursal',
        on_delete=models.CASCADE,
        related_name='transferencias_entrada',
        verbose_name='Sucursal Destino'
    )
    
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='EN_TRANSITO',
        verbose_name='Estado'
    )
    
    motivo = models.TextField(
        blank=True,
        verbose_name='Motivo de Transferencia'
    )
    
    solicitado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transferencias_solicitadas',
        verbose_name='Solicitado Por'
    )
    
    aprobado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferencias_aprobadas',
        verbose_name='Aprobado Por'
    )
    
    recibido_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferencias_recibidas',
        verbose_name='Recibido Por'
    )
    
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Solicitud'
    )
    
    fecha_envio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Envío'
    )
    
    fecha_recepcion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Recepción'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Transferencia entre Sucursales'
        verbose_name_plural = 'Transferencias entre Sucursales'
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.codigo} - {self.producto.nombre} ({self.sucursal_origen} → {self.sucursal_destino})"
    
    def save(self, *args, **kwargs):
        # Generar código automático único
        if not self.codigo:
            import uuid
            self.codigo = f"TRF-{uuid.uuid4().hex[:8].upper()}"  # Ej: TRF-A1B2C3D4
        super().save(*args, **kwargs)

    
    
    def recibir_transferencia(self, usuario):
        """Recibir transferencia en destino"""
        if self.estado != 'EN_TRANSITO':
            raise ValueError("Solo se pueden recibir transferencias en tránsito")
        
        # Agregar a destino
        inv_destino, created = InventarioSucursal.objects.get_or_create(
            producto=self.producto,
            sucursal=self.sucursal_destino,
            defaults={'cantidad': 0, 'cantidad_minima': 5}
        )
        
        inv_destino.cantidad += self.cantidad
        inv_destino.save()
        
        # ✅ Registrar movimiento de entrada
        MovimientoInventario.objects.create(
            producto=self.producto,
            sucursal=self.sucursal_destino,
            tipo='ENTRADA',
            cantidad=self.cantidad,
            motivo=f'Transferencia desde {self.sucursal_origen.nombre} ({self.codigo})',
            usuario=usuario
        )
        
        # Actualizar estado
        self.estado = 'RECIBIDA'
        self.recibido_por = usuario
        self.fecha_recepcion = timezone.now()
        self.save()
class MovimientoInventario(models.Model):
    TIPOS = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    )
    
    # ✅ AMPLIAR MOTIVOS
    MOTIVOS = (
        ('COMPRA', 'Compra'),
        ('VENTA', 'Venta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('AJUSTE', 'Ajuste de inventario'),
        ('MERMA', 'Merma/Pérdida'),
        ('DEVOLUCION', 'Devolución'),
        ('VENCIDO', 'Producto vencido'),
        ('ROBO', 'Robo/Hurto'),
        ('DAÑADO', 'Producto dañado'),
    )
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    motivo = models.CharField(max_length=100, choices=MOTIVOS)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    # ✅ AGREGAR ESTE CAMPO:
    factura = models.ForeignKey(
        'facturas.Factura',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos',
        verbose_name='Factura Asociada'
    )
    
    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cantidad} {self.producto.nombre}"
class AlertaInventario(models.Model):
    TIPOS = (
        ('STOCK_BAJO', 'Stock Bajo'),
        ('SIN_STOCK', 'Sin Stock'),
    )

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    fecha_generada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alerta de Inventario'
        verbose_name_plural = 'Alertas de Inventario'
        ordering = ['-fecha_generada']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre}"





