from django.core.management.base import BaseCommand
from finanzas.models import Gasto, CategoriaGasto
from sucursales.models import Sucursal
from usuarios.models import Usuario
from decimal import Decimal
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Genera gastos de prueba para IA'
    
    def handle(self, *args, **kwargs):
        categorias = list(CategoriaGasto.objects.all())
        usuario = Usuario.objects.filter(rol='SUPER_ADMIN').first()
        sucursal = Sucursal.objects.first()
        
        if not usuario or not sucursal:
            self.stdout.write(self.style.ERROR('❌ No hay usuario SUPER_ADMIN o sucursales'))
            return
        
        # Generar 30 gastos en últimos 3 meses
        for i in range(30):
            fecha = datetime.now() - timedelta(days=random.randint(1, 90))
            
            Gasto.objects.create(
                fecha=fecha.date(),
                sucursal=sucursal,
                categoria=random.choice(categorias),
                concepto=f'Gasto de prueba {i+1}',
                monto=Decimal(random.randint(50000, 500000)),
                metodo_pago=random.choice(['EFECTIVO', 'TRANSFERENCIA', 'TARJETA']),
                estado='APROBADO',
                registrado_por=usuario,
                aprobado_por=usuario,
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ 30 gastos generados'))