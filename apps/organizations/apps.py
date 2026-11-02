from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    name = "apps.organizations"
    label = "organizations"
    verbose_name = "Organizações e RBAC"
    default_auto_field = "django.db.models.BigAutoField"
