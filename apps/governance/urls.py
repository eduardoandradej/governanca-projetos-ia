from django.urls import path

from . import views

app_name = "governance"

P = "projetos/<uuid:project_id>/fases/<uuid:stage_id>/"

urlpatterns = [
    path("gates/", views.approval_queue, name="queue"),
    path("governanca/", views.framework, name="framework"),
    path(P + "gate/solicitar/", views.gate_request, name="request"),
    path(P + "gate/aprovar/", views.gate_approve, name="approve"),
    path(P + "gate/rejeitar/", views.gate_reject, name="reject"),
    path(P + "gate/cancelar/", views.gate_cancel, name="cancel"),
    path(P + "gate/revalidar/", views.gate_revalidate, name="revalidate"),
    path(P + "excecoes/nova/", views.exception_create, name="exception_create"),
    path("gates/excecoes/<uuid:exception_id>/ciencia/", views.exception_ack, name="exception_ack"),
    path("gates/excecoes/<uuid:exception_id>/revogar/", views.exception_revoke, name="exception_revoke"),
]
