from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    name = "apps.integrations"
    label = "integrations"
    verbose_name = "Integrações (futuras, desativadas)"
    default_auto_field = "django.db.models.BigAutoField"
