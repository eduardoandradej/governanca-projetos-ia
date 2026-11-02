from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.organization_list, name="list"),
    path("<uuid:org_id>/", views.organization_detail, name="detail"),
    path("<uuid:org_id>/papeis/<uuid:assignment_id>/revogar/", views.revoke_role, name="revoke_role"),
]
