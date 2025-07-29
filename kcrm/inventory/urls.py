from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.categories, name='categories'),
    path('categories/<int:category_id>/', views.manage_category, name='manage_category'),
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.manage_product, name='manage_product'),
]