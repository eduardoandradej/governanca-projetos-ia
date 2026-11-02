from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("inteligencia/", views.home, name="home"),
    path("inteligencia/indicadores/<str:code>/", views.metric_detail, name="metric"),
    path("inteligencia/regras/executar/", views.run_insights, name="run_insights"),
    path("inteligencia/snapshots/registrar/", views.capture, name="capture"),
    path("inteligencia/insights/", views.insight_list, name="insights"),
    path("inteligencia/insights/<uuid:insight_id>/", views.insight_detail, name="insight"),
    path("inteligencia/insights/<uuid:insight_id>/<str:action>/", views.insight_action, name="insight_action"),
    path("inteligencia/licoes/", views.lesson_list, name="lessons"),
    path("inteligencia/licoes/<uuid:lesson_id>/aprovar/", views.lesson_approve, name="lesson_approve"),
    path("projetos/<uuid:project_id>/dados/", views.project_data, name="project_data"),
    path("projetos/<uuid:project_id>/conhecimento/", views.project_knowledge, name="project_knowledge"),
]
