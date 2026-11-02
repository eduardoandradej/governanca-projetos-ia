from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    name = "apps.analytics"
    label = "analytics"
    verbose_name = "Dados, informação e conhecimento"
    default_auto_field = "django.db.models.BigAutoField"
