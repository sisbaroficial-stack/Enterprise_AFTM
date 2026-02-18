from django.db import models
from django.utils import timezone
from usuarios.models import Usuario
from sucursales.models import Sucursal


class Notificacion(models.Model):
    """
    Sistema de notificaciones para SUPER_ADMIN
    """
    
    TIPOS_NOTIFICACION = [
        # Ventas
        ('VENTA', '🛒 Venta Realizada'),
        ('FACTURA_ANULADA', '❌ Factura Anulada'),
        
        # Inventario
        ('PRODUCTO_CREADO', '📦 Producto Creado'),
        ('PRODUCTO_EDITADO', '✏️ Producto Editado'),
        ('PRODUCTO_ELIMINADO', '🗑️ Producto Eliminado'),
        ('STOCK_AGREGADO', '📈 Stock Agregado'),
        ('STOCK_DESCONTADO', '📉 Stock Descontado'),
        ('AJUSTE_INVENTARIO', '⚖️ Ajuste de Inventario'),
        ('ALERTA_STOCK_BAJO', '⚠️ Stock Bajo'),
        
        # Transferencias
        ('TRANSFERENCIA_CREADA', '🚚 Transferencia Creada'),
        ('TRANSFERENCIA_ENVIADA', '📤 Transferencia Enviada'),
        ('TRANSFERENCIA_RECIBIDA', '📥 Transferencia Recibida'),
        
        # Finanzas
        ('GASTO_REGISTRADO', '💸 Gasto Registrado'),
        ('GASTO_APROBADO', '✅ Gasto Aprobado'),
        ('GASTO_RECHAZADO', '❌ Gasto Rechazado'),
        ('GASTO_PENDIENTE', '⏳ Gasto Pendiente'),
        ('NOMINA_GENERADA', '💰 Nómina Generada'),
        ('EMPLEADO_CREADO', '👤 Empleado Creado'),
        ('EMPLEADO_EDITADO', '✏️ Empleado Editado'),
        
        # Usuarios
        ('USUARIO_REGISTRADO', '👤 Usuario Registrado'),
    ]
    
    tipo = models.CharField(
        max_length=50,
        choices=TIPOS_NOTIFICACION,
        verbose_name='Tipo'
    )
    
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    
    mensaje = models.TextField(
        verbose_name='Mensaje'
    )
    
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Sucursal'
    )
    
    usuario_accion = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acciones_realizadas',
        verbose_name='Usuario'
    )
    
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Monto'
    )
    
    referencia_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Referencia'
    )
    
    referencia_tipo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo Referencia'
    )
    
    leida = models.BooleanField(
        default=False,
        verbose_name='Leída'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha'
    )
    
    fecha_lectura = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha Lectura'
    )
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        sucursal_str = f" - {self.sucursal.nombre}" if self.sucursal else ""
        return f"{self.get_tipo_display()}{sucursal_str}"
    
    def marcar_leida(self):
        if not self.leida:
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save()
    
    @classmethod
    def crear_notificacion(cls, tipo, titulo, mensaje, sucursal=None, usuario=None, monto=None, ref_id=None, ref_tipo=''):
        """Crear notificación fácilmente"""
        try:
            return cls.objects.create(
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                sucursal=sucursal,
                usuario_accion=usuario,
                monto=monto,
                referencia_id=ref_id,
                referencia_tipo=ref_tipo,
            )
        except:
            pass  # No fallar si hay error