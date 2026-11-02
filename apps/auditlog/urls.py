from django.urls import path

from . import views

app_name = "auditlog"

urlpatterns = [
    path("", views.event_list, name="list"),
]
