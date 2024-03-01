from django.urls import path

from pod.quiz.views import create_quiz, to_do

app_name = "quiz"

urlpatterns = [
    path("<slug:video_slug>/", to_do, name="video_quiz"),  # TODO
    path("add/<slug:video_slug>/", create_quiz, name="add_quiz"),
    path("edit/<slug:video_slug>/", to_do, name="edit_quiz"),  # TODO
    path("remove/<slug:video_slug>/", to_do, name="remove_quiz"),  # TODO
]
