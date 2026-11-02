from django.conf import settings
from django.urls import NoReverseMatch, reverse

# Módulos exibidos na navegação quando instalados (incrementos M3–M6).
_MODULES = [
    ("governance:queue", "Gates e aprovações", "/gates/"),
    ("risks:list", "Riscos, custos e decisões", "/riscos/"),
    ("evidence:list", "Documentos e evidências", "/evidencias/"),
    ("analytics:home", "Dados e inteligência", "/inteligencia/"),
    ("governance:framework", "Governança (COBIT/PMBOK)", "/governanca/"),
]


def app_context(request):
    nav = []
    if getattr(request, "user", None) and request.user.is_authenticated:
        for name, label, prefix in _MODULES:
            try:
                nav.append({"url": reverse(name), "label": label, "prefix": prefix})
            except NoReverseMatch:
                continue
    return {
        "APP_NAME": "GovIA",
        "APP_FULL_NAME": "Governança de Projetos de Plataformas de IA",
        "APP_ENVIRONMENT_LABEL": settings.APP_ENVIRONMENT_LABEL,
        "NAV_MODULES": nav,
    }
