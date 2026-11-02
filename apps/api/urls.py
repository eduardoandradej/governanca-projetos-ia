from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("projetos", views.ProjectViewSet, basename="project")
router.register("riscos", views.RiskViewSet, basename="risk")
router.register("decisoes", views.DecisionViewSet, basename="decision")

app_name = "api"

urlpatterns = [
    path("indicadores/", views.metrics_view, name="metrics"),
    path("", include(router.urls)),
]
