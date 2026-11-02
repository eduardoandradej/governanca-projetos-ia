from django.urls import path

from . import views

app_name = "risks"

urlpatterns = [
    path("riscos/", views.risk_overview, name="list"),
    path("riscos/<uuid:risk_id>/", views.risk_detail, name="detail"),
    path("riscos/<uuid:risk_id>/tratamento/", views.risk_treatment, name="treatment"),
    path("riscos/<uuid:risk_id>/reavaliar/", views.risk_reassess, name="reassess"),
    path("riscos/<uuid:risk_id>/aceitar-residual/", views.risk_accept, name="accept"),
    path("projetos/<uuid:project_id>/riscos/", views.project_risks, name="project"),
    path("projetos/<uuid:project_id>/custos/", views.project_costs, name="costs"),
    path("projetos/<uuid:project_id>/decisoes/", views.project_decisions, name="decisions"),
    path("decisoes/<uuid:decision_id>/parecer/", views.decision_decide, name="decide"),
    path("decisoes/<uuid:decision_id>/revisar/", views.decision_revise, name="revise"),
]
