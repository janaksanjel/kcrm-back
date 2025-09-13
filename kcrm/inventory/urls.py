from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.categories, name='categories'),
    path('categories/<int:category_id>/', views.manage_category, name='manage_category'),

    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/<int:supplier_id>/', views.manage_supplier, name='manage_supplier'),
    
    path('purchases/', views.purchases, name='purchases'),
    path('purchases/<int:purchase_id>/', views.manage_purchase, name='manage_purchase'),
    path('purchases/<int:purchase_id>/transfer/', views.transfer_to_stock, name='transfer_to_stock'),
    path('purchases/<int:purchase_id>/untransfer/', views.untransfer_from_stock, name='untransfer_from_stock'),
    
    path('stocks/', views.stocks, name='stocks'),
    path('stocks/<int:stock_id>/', views.manage_stock, name='manage_stock'),
    path('stocks/bulk_delete/', views.bulk_delete_stocks, name='bulk_delete_stocks'),
    path('stocks/bulk_create/', views.bulk_create_stocks, name='bulk_create_stocks'),
    
    path('reports/', views.reports, name='reports'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
]