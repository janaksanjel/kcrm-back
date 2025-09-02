from django.db import models
from django.conf import settings

class Role(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana Store'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    emoji = models.CharField(max_length=10, default='👤')
    color = models.CharField(max_length=100, default='from-blue-500 to-indigo-600')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='created_roles')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'mode']

    def __str__(self):
        return f"{self.emoji} {self.name}"

    @property
    def staff_count(self):
        return self.staff_set.count()

class Staff(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana Store'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    shop_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_members')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    restaurant_id = models.IntegerField(null=True, blank=True)
    restaurant_name = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name if self.role else 'No Role'}"
    
    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        user.delete()

class Permission(models.Model):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name='permissions')
    permissions_data = models.JSONField(default=dict)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Permissions for {self.staff.user.get_full_name()}"