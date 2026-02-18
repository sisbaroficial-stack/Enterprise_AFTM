"""
MODELOS DEL MÓDULO DE FINANZAS EMPRESARIALES
Sistema completo de gestión financiera, gastos y nómina
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from sucursales.models import Sucursal
from usuarios.models import Usuario


# ==================== 1. CATEGORÍAS DE GASTOS ====================

class CategoriaGasto(models.Model):
    """
    Categorías para clasificar los gastos operativos
    Ejemplos: Nómina, Arriendo, Servicios Públicos, etc.
    """
    TIPOS = (
        ('FIJO', 'Gasto Fijo'),
        ('VARIABLE', 'Gasto Variable'),
        ('EXCEPCIONAL', 'Gasto Excepcional'),
    )
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la Categoría'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default='VARIABLE',
        verbose_name='Tipo de Gasto'
    )
    
    icono = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Icono Bootstrap',
        help_text='Ej: bi-cash, bi-building, bi-lightning'
    )
    
    color = models.CharField(
        max_length=20,
        default='primary',
        verbose_name='Color',
        help_text='primary, success, danger, warning, info'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Categoría Activa'
    )
    
    orden = models.IntegerField(
        default=0,
        verbose_name='Orden de Visualización'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Categoría de Gasto'
        verbose_name_plural = 'Categorías de Gastos'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


# ==================== 2. GASTOS OPERATIVOS ====================

class Gasto(models.Model):
    """
    Registro individual de cada gasto operativo de la empresa
    """
    ESTADOS = (
        ('PENDIENTE', '⏳ Pendiente Aprobación'),
        ('APROBADO', '✅ Aprobado'),
        ('RECHAZADO', '❌ Rechazado'),
    )
    
    METODOS_PAGO = (
        ('EFECTIVO', '💵 Efectivo'),
        ('TARJETA', '💳 Tarjeta'),
        ('TRANSFERENCIA', '🏦 Transferencia'),
        ('CHEQUE', '📝 Cheque'),
        ('NEQUI', '📱 Nequi'),
        ('DAVIPLATA', '📱 Daviplata'),
        ('OTRO', '🔄 Otro'),
    )
    
    # ===== INFORMACIÓN BÁSICA =====
    fecha = models.DateField(
        default=timezone.now,
        verbose_name='Fecha del Gasto'
    )
    
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos',
        verbose_name='Sucursal',
        help_text='Dejar vacío si es gasto general de la empresa'
    )
    
    categoria = models.ForeignKey(
        CategoriaGasto,
        on_delete=models.PROTECT,
        related_name='gastos',
        verbose_name='Categoría'
    )
    
    concepto = models.CharField(
        max_length=200,
        verbose_name='Concepto/Descripción'
    )
    
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto'
    )
    
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        default='EFECTIVO',
        verbose_name='Método de Pago'
    )
    
    # ===== PROVEEDOR (OPCIONAL) =====
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos',
        verbose_name='Proveedor'
    )
    
    # ===== RECURRENCIA =====
    es_recurrente = models.BooleanField(
        default=False,
        verbose_name='Es Gasto Recurrente',
        help_text='Se repite mensualmente'
    )
    
    # ===== FACTURA/RECIBO =====
    numero_factura = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Número de Factura/Recibo'
    )
    
    factura_adjunta = models.FileField(
        upload_to='gastos/facturas/',
        blank=True,
        null=True,
        verbose_name='Factura/Recibo Adjunto'
    )
    
    # ===== NOTAS =====
    notas = models.TextField(
        blank=True,
        verbose_name='Notas Adicionales'
    )
    
    # ===== ESTADO Y APROBACIÓN =====
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE',
        verbose_name='Estado'
    )
    
    # ===== AUDITORÍA =====
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='gastos_registrados',
        verbose_name='Registrado Por'
    )
    
    aprobado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos_aprobados',
        verbose_name='Aprobado Por'
    )
    
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )
    
    fecha_aprobacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Aprobación'
    )
    
    motivo_rechazo = models.TextField(
        blank=True,
        verbose_name='Motivo de Rechazo'
    )
    
    ultima_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Modificación'
    )
    
    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-fecha', '-fecha_registro']
        indexes = [
            models.Index(fields=['fecha', 'sucursal']),
            models.Index(fields=['estado']),
            models.Index(fields=['categoria']),
        ]
    
    def __str__(self):
        sucursal_str = self.sucursal.nombre if self.sucursal else 'General'
        return f"{self.fecha} - {self.concepto} - ${self.monto:,.0f} ({sucursal_str})"
    
    def aprobar(self, usuario):
        """Aprobar el gasto"""
        self.estado = 'APROBADO'
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.save()
    
    def rechazar(self, usuario, motivo):
        """Rechazar el gasto"""
        self.estado = 'RECHAZADO'
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.motivo_rechazo = motivo
        self.save()
    
    @property
    def requiere_aprobacion(self):
        """¿Requiere aprobación de SUPER_ADMIN?"""
        return self.monto >= Decimal('100000')
    
    @property
    def dias_desde_registro(self):
        """Días transcurridos desde el registro"""
        return (timezone.now() - self.fecha_registro).days


# ==================== 3. GASTOS RECURRENTES ====================

class GastoRecurrente(models.Model):
    """
    Plantilla de gastos que se repiten mensualmente
    Ej: Arriendo, Internet, Nómina base, etc.
    """
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Gasto Recurrente'
    )
    
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='gastos_recurrentes',
        verbose_name='Sucursal'
    )
    
    categoria = models.ForeignKey(
        CategoriaGasto,
        on_delete=models.PROTECT,
        related_name='gastos_recurrentes',
        verbose_name='Categoría'
    )
    
    monto_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto Base Mensual'
    )
    
    metodo_pago = models.CharField(
        max_length=20,
        choices=Gasto.METODOS_PAGO,
        default='TRANSFERENCIA',
        verbose_name='Método de Pago Habitual'
    )
    
    dia_pago = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        default=1,
        verbose_name='Día del Mes para Pago',
        help_text='Día en que se realiza el pago (1-31)'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Gasto Activo'
    )
    
    auto_crear = models.BooleanField(
        default=True,
        verbose_name='Crear Automáticamente',
        help_text='Crear gasto automáticamente cada mes'
    )
    
    requiere_aprobacion = models.BooleanField(
        default=False,
        verbose_name='Requiere Aprobación Manual'
    )
    
    notas = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Creado Por'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Gasto Recurrente'
        verbose_name_plural = 'Gastos Recurrentes'
        ordering = ['sucursal', 'dia_pago']
    
    def __str__(self):
        sucursal_str = self.sucursal.nombre if self.sucursal else 'General'
        return f"{self.nombre} - ${self.monto_base:,.0f} ({sucursal_str})"


# ==================== 4. EMPLEADOS ====================

class Empleado(models.Model):
    """
    Información completa de empleados
    """
    TIPOS_DOCUMENTO = (
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('TI', 'Tarjeta de Identidad'),
        ('PP', 'Pasaporte'),
    )
    
    TIPOS_CONTRATO = (
        ('INDEFINIDO', 'Término Indefinido'),
        ('FIJO', 'Término Fijo'),
        ('OBRA', 'Obra o Labor'),
        ('PRESTACION', 'Prestación de Servicios'),
    )
    
    ESTADOS = (
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
        ('VACACIONES', 'De Vacaciones'),
        ('LICENCIA', 'En Licencia'),
        ('RETIRADO', 'Retirado'),
    )
    
    # ===== INFORMACIÓN PERSONAL =====
    tipo_documento = models.CharField(
        max_length=3,
        choices=TIPOS_DOCUMENTO,
        default='CC',
        verbose_name='Tipo de Documento'
    )
    
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de Documento'
    )
    
    nombres = models.CharField(
        max_length=100,
        verbose_name='Nombres'
    )
    
    apellidos = models.CharField(
        max_length=100,
        verbose_name='Apellidos'
    )
    
    fecha_nacimiento = models.DateField(
        verbose_name='Fecha de Nacimiento'
    )
    
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono'
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )
    
    direccion = models.TextField(
        verbose_name='Dirección'
    )
    
    ciudad = models.CharField(
        max_length=100,
        default='Bogotá',
        verbose_name='Ciudad'
    )
    
    # ===== INFORMACIÓN LABORAL =====
    cargo = models.CharField(
        max_length=100,
        verbose_name='Cargo'
    )
    
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name='empleados',
        verbose_name='Sucursal'
    )
    
    tipo_contrato = models.CharField(
        max_length=20,
        choices=TIPOS_CONTRATO,
        default='INDEFINIDO',
        verbose_name='Tipo de Contrato'
    )
    
    fecha_ingreso = models.DateField(
        verbose_name='Fecha de Ingreso'
    )
    
    fecha_retiro = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Retiro'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='ACTIVO',
        verbose_name='Estado'
    )
    
    # ===== INFORMACIÓN SALARIAL =====
    salario_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Salario Base Mensual'
    )
    
    auxilio_transporte = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('162000'),  # 2026
        verbose_name='Auxilio de Transporte',
        help_text='Actualizar según año vigente'
    )
    
    # ===== RELACIÓN CON USUARIO DEL SISTEMA =====
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empleado',
        verbose_name='Usuario del Sistema',
        help_text='Si tiene acceso al sistema'
    )
    
    # ===== AUDITORÍA =====
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='empleados_creados',
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
    
    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['apellidos', 'nombres']
    
    def __str__(self):
        return f"{self.apellidos} {self.nombres} - {self.cargo}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def edad(self):
        """Calcular edad actual"""
        hoy = timezone.now().date()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    @property
    def dias_trabajados(self):
        """Días trabajados en la empresa"""
        if self.fecha_retiro:
            return (self.fecha_retiro - self.fecha_ingreso).days
        return (timezone.now().date() - self.fecha_ingreso).days
    
    @property
    def anos_trabajados(self):
        """Años trabajados (para prestaciones)"""
        return self.dias_trabajados / 365.25


# ==================== 5. NÓMINA ====================

class Nomina(models.Model):
    """
    Nómina mensual de empleados con cálculos automáticos
    """
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='nominas',
        verbose_name='Empleado'
    )
    
    mes = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name='Mes'
    )
    
    anio = models.IntegerField(
        validators=[MinValueValidator(2020)],
        verbose_name='Año'
    )
    
    # ===== DEVENGADO =====
    salario_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Salario Base'
    )
    
    auxilio_transporte = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Auxilio de Transporte'
    )
    
    horas_extras = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Horas Extras'
    )
    
    bonificaciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Bonificaciones'
    )
    
    comisiones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Comisiones'
    )
    
    total_devengado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Total Devengado'
    )
    
    # ===== DEDUCCIONES =====
    salud = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Salud (4%)'
    )
    
    pension = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Pensión (4%)'
    )
    
    prestamos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Préstamos'
    )
    
    otras_deducciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Otras Deducciones'
    )
    
    total_deducciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Total Deducciones'
    )
    
    # ===== NETO A PAGAR =====
    neto_pagar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Neto a Pagar'
    )
    
    # ===== APORTES PATRONALES (NO VISIBLE AL EMPLEADO) =====
    salud_empresa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Salud Empresa (8.5%)'
    )
    
    pension_empresa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Pensión Empresa (12%)'
    )
    
    arl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='ARL (0.522%)'
    )
    
    caja_compensacion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Caja Compensación (4%)'
    )
    
    icbf = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='ICBF (3%)'
    )
    
    sena = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='SENA (2%)'
    )
    
    total_aportes_empresa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total Aportes Empresa'
    )
    
    # ===== COSTO TOTAL PARA LA EMPRESA =====
    costo_total_empresa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Costo Total Empresa'
    )
    
    # ===== ESTADO Y PAGO =====
    pagado = models.BooleanField(
        default=False,
        verbose_name='Pagado'
    )
    
    fecha_pago = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Pago'
    )
    
    metodo_pago = models.CharField(
        max_length=20,
        choices=Gasto.METODOS_PAGO,
        default='TRANSFERENCIA',
        verbose_name='Método de Pago'
    )
    
    notas = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    # ===== AUDITORÍA =====
    generado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='nominas_generadas',
        verbose_name='Generado Por'
    )
    
    fecha_generacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Generación'
    )
    
    class Meta:
        verbose_name = 'Nómina'
        verbose_name_plural = 'Nóminas'
        unique_together = ['empleado', 'mes', 'anio']
        ordering = ['-anio', '-mes', 'empleado__apellidos']
    
    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.mes}/{self.anio} - ${self.neto_pagar:,.0f}"
    
    def calcular_totales(self):
        """
        Calcular todos los totales automáticamente
        Según normativa Colombia 2026
        """
        # DEVENGADO
        self.total_devengado = (
            self.salario_base +
            self.auxilio_transporte +
            self.horas_extras +
            self.bonificaciones +
            self.comisiones
        )
        
        # DEDUCCIONES DEL EMPLEADO (sobre salario base)
        base_calculo = self.salario_base
        self.salud = base_calculo * Decimal('0.04')  # 4%
        self.pension = base_calculo * Decimal('0.04')  # 4%
        
        self.total_deducciones = (
            self.salud +
            self.pension +
            self.prestamos +
            self.otras_deducciones
        )
        
        # NETO A PAGAR
        self.neto_pagar = self.total_devengado - self.total_deducciones
        
        # APORTES PATRONALES (Colombia 2026)
        self.salud_empresa = base_calculo * Decimal('0.085')  # 8.5%
        self.pension_empresa = base_calculo * Decimal('0.12')  # 12%
        self.arl = base_calculo * Decimal('0.00522')  # 0.522%
        self.caja_compensacion = base_calculo * Decimal('0.04')  # 4%
        self.icbf = base_calculo * Decimal('0.03')  # 3%
        self.sena = base_calculo * Decimal('0.02')  # 2%
        
        self.total_aportes_empresa = (
            self.salud_empresa +
            self.pension_empresa +
            self.arl +
            self.caja_compensacion +
            self.icbf +
            self.sena
        )
        
        # COSTO TOTAL PARA LA EMPRESA
        self.costo_total_empresa = (
            self.salario_base +
            self.auxilio_transporte +
            self.horas_extras +
            self.bonificaciones +
            self.comisiones +
            self.total_aportes_empresa
        )
        
        self.save()


# ==================== 6. ASISTENCIA ====================

class Asistencia(models.Model):
    """
    Control de asistencia de empleados
    """
    TIPOS = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    )
    
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='asistencias',
        verbose_name='Empleado'
    )
    
    fecha = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    
    hora = models.TimeField(
        verbose_name='Hora'
    )
    
    tipo = models.CharField(
        max_length=10,
        choices=TIPOS,
        verbose_name='Tipo'
    )
    
    notas = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Registrado Por'
    )
    
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )
    
    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        ordering = ['-fecha', '-hora']
    
    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.fecha} {self.tipo}"


# ==================== 7. VACACIONES ====================

class Vacacion(models.Model):
    """
    Solicitudes y aprobaciones de vacaciones
    """
    ESTADOS = (
        ('PENDIENTE', '⏳ Pendiente'),
        ('APROBADA', '✅ Aprobada'),
        ('RECHAZADA', '❌ Rechazada'),
        ('EN_CURSO', '🏖️ En Curso'),
        ('FINALIZADA', '✔️ Finalizada'),
    )
    
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='vacaciones',
        verbose_name='Empleado'
    )
    
    fecha_inicio = models.DateField(
        verbose_name='Fecha de Inicio'
    )
    
    fecha_fin = models.DateField(
        verbose_name='Fecha de Fin'
    )
    
    dias_totales = models.IntegerField(
        verbose_name='Días Totales'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE',
        verbose_name='Estado'
    )
    
    motivo = models.TextField(
        blank=True,
        verbose_name='Motivo/Observaciones'
    )
    
    aprobado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacaciones_aprobadas',
        verbose_name='Aprobado Por'
    )
    
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Solicitud'
    )
    
    fecha_aprobacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Aprobación'
    )
    
    class Meta:
        verbose_name = 'Vacación'
        verbose_name_plural = 'Vacaciones'
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.fecha_inicio} a {self.fecha_fin}"
    
    def save(self, *args, **kwargs):
        # Calcular días totales automáticamente
        if self.fecha_inicio and self.fecha_fin:
            self.dias_totales = (self.fecha_fin - self.fecha_inicio).days + 1
        super().save(*args, **kwargs)


# ==================== 8. PRESUPUESTO ====================

class Presupuesto(models.Model):
    """
    Presupuestos mensuales por categoría
    """
    categoria = models.ForeignKey(
        CategoriaGasto,
        on_delete=models.CASCADE,
        related_name='presupuestos',
        verbose_name='Categoría'
    )
    
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='presupuestos',
        verbose_name='Sucursal',
        help_text='Dejar vacío para presupuesto global'
    )
    
    mes = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name='Mes'
    )
    
    anio = models.IntegerField(
        validators=[MinValueValidator(2020)],
        verbose_name='Año'
    )
    
    monto_presupuestado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Monto Presupuestado'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    notas = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Creado Por'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        unique_together = ['categoria', 'sucursal', 'mes', 'anio']
        ordering = ['-anio', '-mes']
    
    def __str__(self):
        sucursal_str = self.sucursal.nombre if self.sucursal else 'Global'
        return f"{self.categoria.nombre} - {self.mes}/{self.anio} ({sucursal_str}) - ${self.monto_presupuestado:,.0f}"
    
    @property
    def gastado(self):
        """Calcular lo gastado en este presupuesto"""
        gastos = Gasto.objects.filter(
            categoria=self.categoria,
            fecha__year=self.anio,
            fecha__month=self.mes,
            estado='APROBADO'
        )
        
        if self.sucursal:
            gastos = gastos.filter(sucursal=self.sucursal)
        
        from django.db.models import Sum
        total = gastos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        return total
    
    @property
    def disponible(self):
        """Monto disponible del presupuesto"""
        return self.monto_presupuestado - self.gastado
    
    @property
    def porcentaje_usado(self):
        """Porcentaje usado del presupuesto"""
        if self.monto_presupuestado > 0:
            return (self.gastado / self.monto_presupuestado * 100)
        return 0
    
    @property
    def estado_presupuesto(self):
        """Estado del presupuesto según % usado"""
        porcentaje = self.porcentaje_usado
        if porcentaje >= 100:
            return 'EXCEDIDO'
        elif porcentaje >= 90:
            return 'CRITICO'
        elif porcentaje >= 75:
            return 'ALERTA'
        else:
            return 'NORMAL'


# ==================== 9. ANÁLISIS FINANCIERO (CACHE IA) ====================

class AnalisisFinanciero(models.Model):
    """
    Cache de análisis financieros con IA
    Para no recalcular cada vez
    """
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analisis_financieros',
        verbose_name='Sucursal',
        help_text='Null = análisis global'
    )
    
    mes = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name='Mes'
    )
    
    anio = models.IntegerField(
        validators=[MinValueValidator(2020)],
        verbose_name='Año'
    )
    
    # ===== DATOS CALCULADOS =====
    total_ventas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total Ventas'
    )
    
    costo_mercancia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Costo de Mercancía'
    )
    
    utilidad_bruta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Utilidad Bruta'
    )
    
    total_gastos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total Gastos'
    )
    
    utilidad_neta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Utilidad Neta'
    )
    
    margen_bruto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Margen Bruto (%)'
    )
    
    margen_neto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Margen Neto (%)'
    )
    
    # ===== PREDICCIONES IA =====
    datos_ia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos de IA',
        help_text='Predicciones, anomalías, tendencias'
    )
    
    # ===== META =====
    fecha_calculo = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Cálculo'
    )
    
    class Meta:
        verbose_name = 'Análisis Financiero'
        verbose_name_plural = 'Análisis Financieros'
        unique_together = ['sucursal', 'mes', 'anio']
        ordering = ['-anio', '-mes']
    
    def __str__(self):
        sucursal_str = self.sucursal.nombre if self.sucursal else 'Global'
        return f"{sucursal_str} - {self.mes}/{self.anio}"
