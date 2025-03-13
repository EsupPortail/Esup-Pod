from django.urls import path
from . import views

app_name = 'hyperlinks'

urlpatterns = [
    path('', views.manage_hyperlinks, name='manage_hyperlinks'),
    path('add/', views.add_hyperlink, name='add_hyperlink'),
    path('edit/<int:hyperlink_id>/', views.edit_hyperlink, name='edit_hyperlink'),
    path('delete/<int:hyperlink_id>/', views.delete_hyperlink, name='delete_hyperlink'),
    path('manage/', views.manage_hyperlinks, name='hyperlinks_management'),
]
