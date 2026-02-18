"""
Comando para cargar categorías de gastos predefinidas
"""

from django.core.management.base import BaseCommand
from finanzas.models import CategoriaGasto


class Command(BaseCommand):
    help = 'Carga las categorías de gastos predefinidas para Colombia'
    
    def handle(self, *args, **kwargs):
        categorias = [
            # GASTOS FIJOS
            {'nombre': 'Nómina y Personal', 'tipo': 'FIJO', 'icono': 'bi-people', 'color': 'primary', 'orden': 1},
            {'nombre': 'Arriendo y Alquiler', 'tipo': 'FIJO', 'icono': 'bi-building', 'color': 'info', 'orden': 2},
            {'nombre': 'Seguros', 'tipo': 'FIJO', 'icono': 'bi-shield-check', 'color': 'success', 'orden': 3},
            {'nombre': 'Software y Licencias', 'tipo': 'FIJO', 'icono': 'bi-laptop', 'color': 'secondary', 'orden': 4},
            {'nombre': 'Contador/Revisor Fiscal', 'tipo': 'FIJO', 'icono': 'bi-calculator', 'color': 'dark', 'orden': 5},
            
            # GASTOS VARIABLES
            {'nombre': 'Servicios Públicos', 'tipo': 'VARIABLE', 'icono': 'bi-lightning', 'color': 'warning', 'orden': 10},
            {'nombre': 'Transporte y Logística', 'tipo': 'VARIABLE', 'icono': 'bi-truck', 'color': 'primary', 'orden': 11},
            {'nombre': 'Publicidad y Marketing', 'tipo': 'VARIABLE', 'icono': 'bi-megaphone', 'color': 'danger', 'orden': 12},
            {'nombre': 'Mantenimiento y Reparaciones', 'tipo': 'VARIABLE', 'icono': 'bi-tools', 'color': 'secondary', 'orden': 13},
            {'nombre': 'Insumos Operativos', 'tipo': 'VARIABLE', 'icono': 'bi-box-seam', 'color': 'info', 'orden': 14},
            {'nombre': 'Papelería y Oficina', 'tipo': 'VARIABLE', 'icono': 'bi-file-text', 'color': 'secondary', 'orden': 15},
            {'nombre': 'Aseo y Cafetería', 'tipo': 'VARIABLE', 'icono': 'bi-cup-straw', 'color': 'success', 'orden': 16},
            {'nombre': 'Capacitación', 'tipo': 'VARIABLE', 'icono': 'bi-book', 'color': 'primary', 'orden': 17},
            
            # GASTOS ADMINISTRATIVOS
            {'nombre': 'Impuestos', 'tipo': 'VARIABLE', 'icono': 'bi-receipt', 'color': 'danger', 'orden': 20},
            {'nombre': 'Gastos Bancarios', 'tipo': 'VARIABLE', 'icono': 'bi-bank', 'color': 'warning', 'orden': 21},
            {'nombre': 'Asesoría Legal', 'tipo': 'VARIABLE', 'icono': 'bi-briefcase', 'color': 'dark', 'orden': 22},
            
            # OTROS
            {'nombre': 'Donaciones', 'tipo': 'EXCEPCIONAL', 'icono': 'bi-gift', 'color': 'success', 'orden': 30},
            {'nombre': 'Multas y Sanciones', 'tipo': 'EXCEPCIONAL', 'icono': 'bi-exclamation-triangle', 'color': 'danger', 'orden': 31},
            {'nombre': 'Imprevistos', 'tipo': 'EXCEPCIONAL', 'icono': 'bi-question-circle', 'color': 'secondary', 'orden': 32},
        ]
        
        creadas = 0
        actualizadas = 0
        
        for cat_data in categorias:
            categoria, created = CategoriaGasto.objects.update_or_create(
                nombre=cat_data['nombre'],
                defaults={
                    'tipo': cat_data['tipo'],
                    'icono': cat_data['icono'],
                    'color': cat_data['color'],
                    'orden': cat_data['orden'],
                    'activa': True,
                }
            )
            
            if created:
                creadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Creada: {categoria.nombre}')
                )
            else:
                actualizadas += 1
                self.stdout.write(
                    self.style.WARNING(f'♻️ Actualizada: {categoria.nombre}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Proceso completado: {creadas} creadas, {actualizadas} actualizadas')
        )