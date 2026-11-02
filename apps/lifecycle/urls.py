from django.urls import path

from . import views

app_name = "lifecycle"

urlpatterns = [
    path("<uuid:project_id>/fases/<uuid:stage_id>/", views.stage_detail, name="stage"),
    path("<uuid:project_id>/fases/<uuid:stage_id>/retomar/", views.stage_resume, name="stage_resume"),
    path(
        "<uuid:project_id>/fases/<uuid:stage_id>/requisitos/<uuid:requirement_id>/atender/",
        views.requirement_fulfill, name="requirement_fulfill",
    ),
    path(
        "<uuid:project_id>/fases/<uuid:stage_id>/requisitos/<uuid:requirement_id>/validar/",
        views.requirement_validate, name="requirement_validate",
    ),
    path("<uuid:project_id>/fases/<uuid:stage_id>/tarefas/nova/", views.task_create, name="task_create"),
    path("<uuid:project_id>/tarefas/", views.task_board, name="tasks"),
    path("<uuid:project_id>/tarefas/<uuid:task_id>/status/", views.task_status, name="task_status"),
]
