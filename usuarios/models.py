from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado con roles específicos para SISBAR
    """

    ROLES = (
        ('SUPER_ADMIN', '👑 Super Administrador '),
        ('ADMIN', '👨‍💼 Administrador'),
        ('EMPLEADO', '👤 Empleado'),
        ('AUDITOR', '👁️ Auditor/Contador'),
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='EMPLEADO',
        verbose_name='Rol'
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )

    documento = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Documento de Identidad'
    )

    foto_perfil = models.ImageField(
        upload_to='usuarios/perfiles/',
        blank=True,
        null=True,
        verbose_name='Foto de Perfil'
    )

    aprobado = models.BooleanField(
        default=False,
        verbose_name='Cuenta Aprobada',
        help_text='El usuario debe ser aprobado por un administrador'
    )

    fecha_aprobacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de Aprobación'
    )

    aprobado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_aprobados',
        verbose_name='Aprobado Por'
    )

    notificado_aprobacion = models.BooleanField(
        default=False,
        verbose_name='Correo de aprobación enviado'
    )

    modo_oscuro = models.BooleanField(
        default=False,
        verbose_name='Modo Oscuro Activado'
    )

    ultima_actividad = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actividad'
    )

    # 🔹 Aquí agregamos la sucursal usando referencia en cadena
    sucursal = models.ForeignKey(
        'sucursales.Sucursal',  # <-- referencia en cadena, no import directo
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sucursal asignada"
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
        permissions = [
            ('puede_aprobar_usuarios', 'Puede aprobar nuevos usuarios'),
            ('puede_ver_reportes', 'Puede ver reportes completos'),
            ('puede_eliminar_productos', 'Puede eliminar productos'),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    def aprobar_usuario(self, aprobador):
        """Aprobar un usuario pendiente"""
        self.aprobado = True
        self.fecha_aprobacion = timezone.now()
        self.aprobado_por = aprobador
        self.save()

    def puede_gestionar_inventario(self):
        """Verifica si el usuario puede gestionar inventario"""
        return self.rol in ['SUPER_ADMIN', 'ADMIN', 'EMPLEADO']

    def puede_eliminar(self):
        """Verifica si el usuario puede eliminar registros"""
        return self.rol in ['SUPER_ADMIN', 'ADMIN']

    def puede_aprobar(self):
        """Verifica si el usuario puede aprobar otros usuarios"""
        return self.rol in ['SUPER_ADMIN', 'ADMIN']


class HistorialActividad(models.Model):
    """
    Registro de actividades de los usuarios para auditoría
    """

    TIPOS_ACTIVIDAD = (
        ('LOGIN', 'Inicio de Sesión'),
        ('LOGOUT', 'Cierre de Sesión'),
        ('CREAR', 'Creación de Registro'),
        ('EDITAR', 'Edición de Registro'),
        ('ELIMINAR', 'Eliminación de Registro'),
        ('DESCONTAR', 'Descuento de Producto'),
        ('EXPORTAR', 'Exportación de Reporte'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='actividades',
        verbose_name='Usuario'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_ACTIVIDAD,
        verbose_name='Tipo de Actividad'
    )

    descripcion = models.TextField(
        verbose_name='Descripción'
    )

    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y Hora'
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='Dirección IP'
    )

    class Meta:
        verbose_name = 'Historial de Actividad'
        verbose_name_plural = 'Historial de Actividades'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} - {self.fecha}"
