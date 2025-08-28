from django.urls import path
from . import views

urlpatterns = [
    # Role management
    path('roles/', views.roles, name='roles'),
    path('roles/<int:role_id>/', views.manage_role, name='manage_role'),
    path('permissions/', views.permissions, name='permissions'),
    path('roles/assign/', views.assign_role, name='assign_role'),
    path('users/<int:user_id>/roles/', views.user_roles, name='user_roles'),
]