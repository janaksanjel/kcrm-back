from django.urls import path
from . import views

urlpatterns = [
    # Auth endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('super-admin/register/', views.super_admin_register, name='super_admin_register'),
    
    # Settings endpoints
    path('settings/profile/', views.update_profile, name='update_profile'),
    path('settings/password/', views.change_password, name='change_password'),
    path('settings/sessions/', views.get_sessions, name='get_sessions'),
    path('settings/sessions/<int:session_id>/', views.terminate_session, name='terminate_session'),
    path('settings/sessions/terminate-all/', views.terminate_all_sessions, name='terminate_all_sessions'),
    path('settings/economic-years/', views.economic_years, name='economic_years'),
    path('settings/economic-years/<int:year_id>/', views.manage_economic_year, name='manage_economic_year'),
    path('settings/economic-years/<int:year_id>/toggle/', views.toggle_economic_year, name='toggle_economic_year'),
    path('header/economic-years/', views.header_economic_years, name='header_economic_years'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('settings/security/', views.security_settings, name='security_settings'),
    path('settings/security/activity/', views.get_security_activity, name='get_security_activity'),
    
    # Kitchen user management
    path('kitchen-users/create/', views.create_kitchen_user, name='create_kitchen_user'),
    path('kitchen-users/', views.get_kitchen_users, name='get_kitchen_users'),
    path('kitchen-users/<int:user_id>/delete/', views.delete_kitchen_user, name='delete_kitchen_user'),
]