from django.urls import path
from .views import (
    admin_dashboard_view,
    admin_question_add,
    admin_question_delete,
    admin_question_edit,
    dashboard_view,
    landing_view,
    quiz_question_view,
    quiz_start_view,
    quiz_submit_view,
    ressources_view,
    results_view,
)

urlpatterns = [
    path("", landing_view, name="landing"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("quiz/start/", quiz_start_view, name="quiz_start"),
    path("quiz/question/<int:numero>/", quiz_question_view, name="quiz_question"),
    path("quiz/submit/", quiz_submit_view, name="quiz_submit"),
    path("results/<int:session_id>/", results_view, name="results"),
    path("admin-dashboard/", admin_dashboard_view, name="admin_dashboard"),
    path("admin/question/add/", admin_question_add, name="admin_question_add"),
    path("admin/question/<int:question_id>/edit/", admin_question_edit, name="admin_question_edit"),
    path("admin/question/<int:question_id>/delete/", admin_question_delete, name="admin_question_delete"),
    path("ressources/", ressources_view, name="ressources"),
]
