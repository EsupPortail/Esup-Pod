from django.urls import path

from . import views

app_name = 'meeting'

urlpatterns = [
    path('', views.my_meetings, name='my_meetings'),
    path('<slug:meeting_id>/', views.join, name='join'),
    path('add/', views.add, name='add'),
]
