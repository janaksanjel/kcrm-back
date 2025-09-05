from django.urls import path
from . import views

urlpatterns = [
    path('shop-owners/', views.get_shop_owners, name='get_shop_owners'),
    path('shop-owners/<int:user_id>/approve/', views.approve_shop_owner, name='approve_shop_owner'),
    path('shop-owners/<int:user_id>/reject/', views.reject_shop_owner, name='reject_shop_owner'),
    path('shop-owners/<int:user_id>/delete/', views.delete_shop_owner, name='delete_shop_owner'),
    path('shop-owners/<int:user_id>/password/', views.change_password, name='change_password'),
    path('shop-owners/<int:user_id>/permissions/', views.manage_permissions, name='manage_permissions'),
    path('shop-owners/<int:user_id>/save-permissions/', views.save_permissions, name='save_permissions'),
    path('available-modes/', views.get_available_modes, name='get_available_modes'),
    path('user-permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('dashboard-stats/', views.get_dashboard_stats, name='get_dashboard_stats'),
]