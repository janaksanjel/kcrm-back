from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SaleViewSet, StockViewSet, ProfitPercentageViewSet, MenuCategoryViewSet, MenuItemViewSet


router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'sales', SaleViewSet)
router.register(r'stocks', StockViewSet, basename='stocks')
router.register(r'menu-categories', MenuCategoryViewSet)
router.register(r'menu-items', MenuItemViewSet)
router.register(r'profit-percentage', ProfitPercentageViewSet, basename='profit-percentage')


urlpatterns = [
    path('', include(router.urls)),
]