from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="list"),
    path("novo/<uuid:org_id>/", views.project_create, name="create"),
    path("<uuid:project_id>/", views.project_detail, name="detail"),
    path("<uuid:project_id>/editar/", views.project_edit, name="edit"),
    path("<uuid:project_id>/status/", views.project_status, name="status"),
]
