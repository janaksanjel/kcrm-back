from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ReportData(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana Store'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    REPORT_TYPES = [
        ('sales', 'Sales'),
        ('inventory', 'Inventory'),
        ('financial', 'Financial'),
        ('customer', 'Customer'),
        ('performance', 'Performance'),
        ('trends', 'Trends'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'mode', 'report_type']