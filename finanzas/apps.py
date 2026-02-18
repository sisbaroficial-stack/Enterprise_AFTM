from django.apps import AppConfig


class FinanzasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finanzas'
    verbose_name = '💰 Finanzas Empresariales'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import finanzas.signals