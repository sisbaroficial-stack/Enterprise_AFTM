from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.text import slugify

class Empresa(models.Model):
    """
    Modelo central del Multi-Tenant.
    TODAS las empresas del sistema SaaS.
    """
    
    # ============ IDENTIFICACIÓN ============
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre Comercial',
        help_text='Nombre que aparecerá en el sistema'
    )
    
    razon_social = models.CharField(
        max_length=200,
        verbose_name='Razón Social',
        help_text='Nombre legal de la empresa'
    )
    
    nit = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name='NIT',
        help_text='Número de Identificación Tributaria'
    )
    
    slug = models.SlugField(
        unique=True,
        db_index=True,
        max_length=100,
        verbose_name='Slug',
        help_text='Identificador único para URLs (ej: mi-empresa)'
    )
    
    # ============ PLAN Y FACTURACIÓN ============
    PLANES = [
        ('BASICO', 'Plan Básico - $38.900/mes'),
        ('EMPRENDEDOR', 'Plan Emprendedor - $79.000/mes'),
        ('PROFESIONAL', 'Plan Profesional - $189.000/mes'),
        ('ENTERPRISE', 'Plan Enterprise - Personalizado'),
    ]
    
    plan = models.CharField(
        max_length=20,
        choices=PLANES,
        default='BASICO',
        verbose_name='Plan Contratado'
    )
    
    activa = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Empresa Activa',
        help_text='Si está desactivada, los usuarios no podrán acceder'
    )
    
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento del Plan',
        help_text='Dejar vacío para plan ilimitado'
    )
    
    # ============ LÍMITES POR PLAN ============
    limite_usuarios = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1)],
        verbose_name='Límite de Usuarios',
        help_text='Cantidad máxima de usuarios activos'
    )
    
    limite_sucursales = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Límite de Sucursales',
        help_text='Cantidad máxima de sucursales'
    )
    
    limite_productos = models.IntegerField(
        default=300,
        validators=[MinValueValidator(1)],
        verbose_name='Límite de Productos',
        help_text='Cantidad máxima de productos en inventario'
    )
    
    # ============ CONTACTO ============
    email_admin = models.EmailField(
        verbose_name='Email del Administrador',
        help_text='Email principal de contacto'
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
    
    # ============ AUDITORÍA ============
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Fecha de Creación'
    )
    
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas_creadas',
        verbose_name='Creado Por'
    )
    
    # ============ PERSONALIZACIÓN ============
    logo = models.ImageField(
        upload_to='empresas/logos/',
        null=True,
        blank=True,
        verbose_name='Logo de la Empresa'
    )
    
    color_primario = models.CharField(
        max_length=7,
        default='#667eea',
        verbose_name='Color Primario',
        help_text='Color en formato hexadecimal (ej: #667eea)'
    )
    
    # ============ NOTAS ============
    notas_internas = models.TextField(
        blank=True,
        verbose_name='Notas Internas',
        help_text='Solo visible para SuperAdmin'
    )
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['nit']),
            models.Index(fields=['activa', '-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.get_plan_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-generar slug si no existe
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
    
    def esta_vencida(self):
        """Verifica si el plan está vencido"""
        if not self.fecha_vencimiento:
            return False
        return timezone.now().date() > self.fecha_vencimiento
    
    def dias_hasta_vencimiento(self):
        """Calcula días restantes hasta el vencimiento"""
        if not self.fecha_vencimiento:
            return None
        delta = self.fecha_vencimiento - timezone.now().date()
        return delta.days
    
    def puede_crear_usuario(self):
        """Verifica si puede crear más usuarios"""
        return self.usuarios.filter(is_active=True).count() < self.limite_usuarios
    
    def puede_crear_sucursal(self):
        """Verifica si puede crear más sucursales"""
        from sucursales.models import Sucursal
        return Sucursal.objects.filter(empresa=self).count() < self.limite_sucursales
    
    def puede_crear_producto(self):
        """Verifica si puede crear más productos"""
        from inventario.models import Producto
        return Producto.objects.filter(empresa=self, activo=True).count() < self.limite_productos
    
    def get_uso_actual(self):
        """Retorna estadísticas de uso actual"""
        from sucursales.models import Sucursal
        from inventario.models import Producto
        
        return {
            'usuarios': self.usuarios.filter(is_active=True).count(),
            'sucursales': Sucursal.objects.filter(empresa=self).count(),
            'productos': Producto.objects.filter(empresa=self, activo=True).count(),
        }
    
    def tiene_acceso_a_modulo(self, modulo):
        """
        Verifica si la empresa tiene acceso a un módulo según su plan.
        
        Módulos por plan:
        - BASICO: inventario, ventas básicas
        - EMPRENDEDOR: + multi-sucursal, reportes básicos
        - PROFESIONAL: + finanzas, IA, nómina
        - ENTERPRISE: + todo ilimitado
        """
        MODULOS_POR_PLAN = {
            'BASICO': ['inventario', 'ventas'],
            'EMPRENDEDOR': ['inventario', 'ventas', 'sucursales', 'reportes_basicos'],
            'PROFESIONAL': ['inventario', 'ventas', 'sucursales', 'reportes_basicos', 
                           'reportes_avanzados', 'finanzas', 'compras_ia', 'nomina'],
            'ENTERPRISE': ['all'],  # Acceso a todo
        }
        
        if self.plan == 'ENTERPRISE':
            return True
        
        return modulo in MODULOS_POR_PLAN.get(self.plan, [])


class AuditoriaLog(models.Model):
    """
    Registro de TODAS las acciones críticas por empresa.
    Sistema de auditoría profesional.
    """
    
    ACCIONES = [
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('VENTA', 'Venta realizada'),
        ('TRANSFERENCIA', 'Transferencia entre sucursales'),
        ('CAMBIO_PRECIO', 'Cambio de precio'),
        ('AJUSTE_INVENTARIO', 'Ajuste de inventario'),
        ('ANULAR_FACTURA', 'Anulación de factura'),
    ]
    
    # ============ RELACIONES ============
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='logs_auditoria',
        verbose_name='Empresa'
    )
    
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_auditoria',
        verbose_name='Usuario'
    )
    
    # ============ DATOS DE ACCIÓN ============
    accion = models.CharField(
        max_length=50,
        choices=ACCIONES,
        verbose_name='Acción'
    )
    
    modelo = models.CharField(
        max_length=100,
        verbose_name='Modelo Afectado',
        help_text='Nombre del modelo (ej: Producto, Venta)'
    )
    
    objeto_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID del Objeto'
    )
    
    # ============ DETALLES ============
    detalles = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Detalles',
        help_text='Información adicional en formato JSON'
    )
    
    ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent',
        help_text='Navegador y dispositivo usado'
    )
    
    # ============ TIMESTAMP ============
    fecha = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Fecha y Hora'
    )
    
    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', '-fecha']),
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['accion', '-fecha']),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else 'Sistema'
        return f"{self.empresa.nombre} - {usuario_str} - {self.get_accion_display()} - {self.fecha}"
    
    @classmethod
    def registrar(cls, empresa, usuario, accion, modelo, objeto_id=None, detalles=None, request=None):
        """
        Helper para registrar acciones fácilmente.
        
        Uso:
        AuditoriaLog.registrar(
            empresa=request.empresa,
            usuario=request.user,
            accion='CREAR',
            modelo='Producto',
            objeto_id=producto.id,
            detalles={'nombre': producto.nombre},
            request=request
        )
        """
        ip = None
        user_agent = ''
        
        if request:
            ip = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(
            empresa=empresa,
            usuario=usuario if usuario and usuario.is_authenticated else None,
            accion=accion,
            modelo=modelo,
            objeto_id=objeto_id,
            detalles=detalles or {},
            ip=ip,
            user_agent=user_agent
        )