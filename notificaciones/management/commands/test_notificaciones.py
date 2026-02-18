"""
SCRIPT DE PRUEBA - SISTEMA DE NOTIFICACIONES
Crea notificaciones de prueba para verificar que todo funciona

USO:
1. Guarda este archivo como: notificaciones/management/commands/test_notificaciones.py
2. Ejecuta: python manage.py test_notificaciones
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from notificaciones.models import Notificacion
from usuarios.models import Usuario
from sucursales.models import Sucursal


class Command(BaseCommand):
    help = 'Crea notificaciones de prueba para verificar el sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🧪 Iniciando pruebas del sistema de notificaciones...'))
        
        # Obtener datos necesarios
        try:
            super_admin = Usuario.objects.filter(rol='SUPER_ADMIN').first()
            sucursal = Sucursal.objects.filter(activa=True).first()
            
            if not super_admin:
                self.stdout.write(self.style.ERROR('❌ No hay usuarios SUPER_ADMIN. Crea uno primero.'))
                return
            
            if not sucursal:
                self.stdout.write(self.style.ERROR('❌ No hay sucursales. Crea una primero.'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario encontrado: {super_admin.username}'))
            self.stdout.write(self.style.SUCCESS(f'✅ Sucursal encontrada: {sucursal.nombre}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error obteniendo datos: {str(e)}'))
            return
        
        # Contador
        notificaciones_creadas = 0
        
        # ===== PRUEBA 1: VENTAS =====
        self.stdout.write('\n📝 Creando notificación de VENTA...')
        try:
            Notificacion.crear_notificacion(
                tipo='VENTA',
                titulo='🛒 Venta #TEST001 - $150,000',
                mensaje=f'{super_admin.get_full_name()} realizó una venta de prueba de $150,000 con 5 productos',
                sucursal=sucursal,
                usuario=super_admin,
                monto=Decimal('150000'),
                ref_id=1,
                ref_tipo='factura'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de VENTA creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 2: FACTURA ANULADA =====
        self.stdout.write('\n📝 Creando notificación de FACTURA ANULADA...')
        try:
            Notificacion.crear_notificacion(
                tipo='FACTURA_ANULADA',
                titulo='❌ Factura Anulada #TEST002',
                mensaje=f'{super_admin.get_full_name()} anuló una factura. Motivo: Error en el registro',
                sucursal=sucursal,
                usuario=super_admin,
                monto=Decimal('50000'),
                ref_id=2,
                ref_tipo='factura'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de FACTURA ANULADA creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 3: PRODUCTO CREADO =====
        self.stdout.write('\n📝 Creando notificación de PRODUCTO CREADO...')
        try:
            Notificacion.crear_notificacion(
                tipo='PRODUCTO_CREADO',
                titulo='📦 Producto Creado: Gaseosa Coca-Cola 2L',
                mensaje=f'{super_admin.get_full_name()} creó el producto "Gaseosa Coca-Cola 2L" (Stock inicial: 100)',
                sucursal=sucursal,
                usuario=super_admin,
                ref_id=1,
                ref_tipo='producto'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de PRODUCTO CREADO creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 4: STOCK AGREGADO =====
        self.stdout.write('\n📝 Creando notificación de STOCK AGREGADO...')
        try:
            Notificacion.crear_notificacion(
                tipo='STOCK_AGREGADO',
                titulo='📈 Stock Agregado: Arroz Diana 500g',
                mensaje=f'{super_admin.get_full_name()} agregó 50 unidades. Stock actual: 150',
                sucursal=sucursal,
                usuario=super_admin,
                ref_id=2,
                ref_tipo='producto'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de STOCK AGREGADO creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 5: TRANSFERENCIA =====
        self.stdout.write('\n📝 Creando notificación de TRANSFERENCIA...')
        try:
            Notificacion.crear_notificacion(
                tipo='TRANSFERENCIA_CREADA',
                titulo=f'🚚 Transferencia {sucursal.nombre} → Otra Sucursal',
                mensaje=f'{super_admin.get_full_name()} envió 20 unidades de "Aceite"',
                sucursal=sucursal,
                usuario=super_admin,
                ref_id=1,
                ref_tipo='transferencia'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de TRANSFERENCIA creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 6: GASTO PENDIENTE =====
        self.stdout.write('\n📝 Creando notificación de GASTO PENDIENTE...')
        try:
            Notificacion.crear_notificacion(
                tipo='GASTO_PENDIENTE',
                titulo='⏳ Gasto Pendiente - $500,000',
                mensaje=f'{super_admin.get_full_name()} registró un gasto de $500,000 que requiere aprobación. Concepto: Reparación de nevera',
                sucursal=sucursal,
                usuario=super_admin,
                monto=Decimal('500000'),
                ref_id=1,
                ref_tipo='gasto'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de GASTO PENDIENTE creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 7: NÓMINA GENERADA =====
        self.stdout.write('\n📝 Creando notificación de NÓMINA GENERADA...')
        try:
            Notificacion.crear_notificacion(
                tipo='NOMINA_GENERADA',
                titulo='💰 Nómina 2/2026 Generada',
                mensaje='5 nóminas generadas. Total: $6,500,000',
                usuario=super_admin,
                monto=Decimal('6500000'),
                ref_tipo='nomina'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de NÓMINA GENERADA creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 8: EMPLEADO CREADO =====
        self.stdout.write('\n📝 Creando notificación de EMPLEADO CREADO...')
        try:
            Notificacion.crear_notificacion(
                tipo='EMPLEADO_CREADO',
                titulo='👤 Empleado Creado: Juan Pérez',
                mensaje=f'{super_admin.get_full_name()} creó el empleado "Juan Pérez" - Vendedor',
                sucursal=sucursal,
                usuario=super_admin,
                ref_id=1,
                ref_tipo='empleado'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de EMPLEADO CREADO creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 9: USUARIO REGISTRADO =====
        self.stdout.write('\n📝 Creando notificación de USUARIO REGISTRADO...')
        try:
            Notificacion.crear_notificacion(
                tipo='USUARIO_REGISTRADO',
                titulo='👤 Nuevo Usuario: María Gómez',
                mensaje='María Gómez (maria@email.com) se registró y espera aprobación',
                usuario=super_admin,
                ref_id=1,
                ref_tipo='usuario'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de USUARIO REGISTRADO creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== PRUEBA 10: ALERTA STOCK BAJO =====
        self.stdout.write('\n📝 Creando notificación de STOCK BAJO...')
        try:
            Notificacion.crear_notificacion(
                tipo='ALERTA_STOCK_BAJO',
                titulo='⚠️ Stock Bajo: Pan Tajado',
                mensaje='El producto "Pan Tajado" tiene stock bajo. Stock actual: 5 unidades',
                sucursal=sucursal,
                ref_id=3,
                ref_tipo='producto'
            )
            notificaciones_creadas += 1
            self.stdout.write(self.style.SUCCESS('  ✅ Notificación de STOCK BAJO creada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # ===== RESUMEN =====
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ PRUEBA COMPLETADA'))
        self.stdout.write(self.style.SUCCESS(f'✅ {notificaciones_creadas} notificaciones creadas exitosamente'))
        self.stdout.write('='*60)
        
        self.stdout.write('\n📋 INSTRUCCIONES PARA VERIFICAR:')
        self.stdout.write('1. Inicia sesión como SUPER_ADMIN')
        self.stdout.write('2. Verás una campanita 🔔 en la esquina superior derecha')
        self.stdout.write('3. Haz clic en la campanita para ver las notificaciones')
        self.stdout.write('4. Deberías ver las 10 notificaciones de prueba')
        self.stdout.write('5. Haz clic en "Ver todas" para ver la lista completa')
        self.stdout.write('\n✅ Si ves todo esto, ¡el sistema funciona correctamente!')