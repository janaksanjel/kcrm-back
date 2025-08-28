from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import EconomicYear
import secrets
import string

User = get_user_model()

class Role(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_roles')
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'mode', 'user', 'economic_year']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.mode})"

class Staff(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='kirana')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_staff')
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    auto_password = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['email', 'created_by', 'economic_year']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.role.name}"
    
    def generate_password(self):
        """Generate a random password"""
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(8))
        return password

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roles_assigned')
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'role']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"