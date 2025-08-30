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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name if self.role else 'No Role'}"