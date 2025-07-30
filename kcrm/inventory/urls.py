from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.categories, name='categories'),
    path('categories/<int:category_id>/', views.manage_category, name='manage_category'),

    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/<int:supplier_id>/', views.manage_supplier, name='manage_supplier'),
    
    path('purchases/', views.purchases, name='purchases'),
    path('purchases/<int:purchase_id>/', views.manage_purchase, name='manage_purchase'),
    
    path('stocks/', views.stocks, name='stocks'),
    path('stocks/<int:stock_id>/', views.manage_stock, name='manage_stock'),
    
    path('reports/', views.reports, name='reports'),
]