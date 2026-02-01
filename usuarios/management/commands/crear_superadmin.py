from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea el SUPER_ADMIN (Dueño) inicial'

    def handle(self, *args, **options):
        Usuario = get_user_model()

        if Usuario.objects.filter(rol='SUPER_ADMIN').exists():
            self.stdout.write(self.style.WARNING('⚠️ Ya existe un SUPER_ADMIN'))
            return

        user = Usuario.objects.create_user(
            username='superadmin',
            email='admin@sisbar.com',
            password='admin123'
        )

        user.rol = 'SUPER_ADMIN'
        user.activo = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS('✅ SUPER_ADMIN creado correctamente'))
