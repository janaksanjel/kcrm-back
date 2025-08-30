from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, StaffViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet)
router.register(r'staff', StaffViewSet)

urlpatterns = [
    path('', include(router.urls)),
]