from django.apps import AppConfig


class AuditlogConfig(AppConfig):
    name = "apps.auditlog"
    label = "auditlog"
    verbose_name = "Trilha de auditoria"
    default_auto_field = "django.db.models.BigAutoField"
