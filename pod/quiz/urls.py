"""Esup-Pod quiz urls."""

from django.urls import path

from pod.quiz.views import edit_quiz, video_quiz, create_quiz, delete_quiz

app_name = "quiz"

urlpatterns = [
    path("<slug:video_slug>/", video_quiz, name="video_quiz"),
    path("add/<slug:video_slug>/", create_quiz, name="add_quiz"),
    path("edit/<slug:video_slug>/", edit_quiz, name="edit_quiz"),
    path("remove/<slug:video_slug>/", delete_quiz, name="remove_quiz"),
]
