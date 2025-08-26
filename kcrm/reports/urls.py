from django.urls import path
from . import views

urlpatterns = [
    path('data/', views.get_reports, name='get_reports'),
]