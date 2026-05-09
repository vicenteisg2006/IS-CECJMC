from django.apps import AppConfig


class AppRelPlusConfig(AppConfig):
    name = 'APP'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import APP.signals  # Importamos los signals para que se registren
