from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ShopOwnerRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_request')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ShopOwnerPermissions(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'mode']