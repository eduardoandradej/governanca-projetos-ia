from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path("contas/", include("apps.accounts.urls")),
    path("organizacoes/", include("apps.organizations.urls")),
    path("projetos/", include("apps.projects.urls")),
    path("projetos/", include("apps.lifecycle.urls")),
    path("", include("apps.governance.urls")),
    path("", include("apps.evidence.urls")),
    path("", include("apps.risks.urls")),
    path("auditoria/", include("apps.auditlog.urls")),
    path("admin-tecnico/", admin.site.urls),
]
