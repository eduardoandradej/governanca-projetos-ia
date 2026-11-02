from django.urls import path

from . import views

app_name = "evidence"

urlpatterns = [
    path("evidencias/", views.evidence_list, name="list"),
    path("evidencias/<uuid:artifact_id>/", views.evidence_detail, name="detail"),
    path("evidencias/<uuid:artifact_id>/versao/", views.evidence_new_version, name="new_version"),
    path("evidencias/<uuid:artifact_id>/inspecionar/", views.evidence_inspect, name="inspect"),
    path("evidencias/<uuid:artifact_id>/revisar/", views.evidence_review, name="review"),
    path("evidencias/<uuid:artifact_id>/arquivar/", views.evidence_archive, name="archive"),
    path("evidencias/<uuid:artifact_id>/baixar/<int:number>/", views.evidence_download, name="download"),
    path("projetos/<uuid:project_id>/evidencias/", views.evidence_list, name="project"),
    path("projetos/<uuid:project_id>/evidencias/nova/", views.evidence_create, name="create"),
]
