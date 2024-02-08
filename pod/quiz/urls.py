from django.urls import path

from pod.quiz.views import to_do

app_name = "quiz"

urlpatterns = [
    path("/<slug:video_slug>/", to_do, name="video_quiz"),  # TODO
    path("add/<slug:video_slug>/", to_do, name="add_quiz"),  # TODO
    path("edit/<slug:video_slug>/", to_do, name="edit_quiz"),  # TODO
    path("remove/<slug:video_slug>/", to_do, name="remove_quiz"),  # TODO
    path("<slug:video_slug>/statistics/", to_do, name="statistics_quiz"),  # TODO
]
