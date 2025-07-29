from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('shop_owner', 'Shop Owner'),
        ('super_admin', 'Super Admin'),
    ]
    
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='shop_owner')
    shop_name = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ShopOwnerFeatures(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='features')
    dashboard = models.BooleanField(default=True)
    inventory = models.BooleanField(default=True)
    billing = models.BooleanField(default=True)
    udhaar = models.BooleanField(default=True)
    expenses = models.BooleanField(default=True)
    reports = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)