from django.urls import path
from .views import (
    dashboard_view,
    landing_view,
    quiz_question_view,
    quiz_start_view,
    quiz_submit_view,
    results_view,
)

urlpatterns = [
    path("", landing_view, name="landing"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("quiz/start/", quiz_start_view, name="quiz_start"),
    path("quiz/question/<int:numero>/", quiz_question_view, name="quiz_question"),
    path("quiz/submit/", quiz_submit_view, name="quiz_submit"),
    path("results/<int:session_id>/", results_view, name="results"),
]
