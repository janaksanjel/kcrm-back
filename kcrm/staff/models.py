from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import EconomicYear

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
    permissions = models.JSONField(default=dict)  # Store permissions as JSON
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'mode', 'user', 'economic_year']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.mode})"

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