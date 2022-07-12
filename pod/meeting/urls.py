from django.urls import path

from . import views

app_name = 'meeting'

urlpatterns = [
    path('', views.my_meetings, name='my_meetings'),
    path('add/', views.add_or_edit, name='add'),
    path('edit/<slug:meeting_id>/', views.add_or_edit, name='edit'),
    path('delete/<slug:meeting_id>/', views.delete, name='delete'),
    path('<slug:meeting_id>/', views.join, name='join'),
    path('<slug:meeting_id>/<slug:direct_access>', views.join, name='join'),
]
