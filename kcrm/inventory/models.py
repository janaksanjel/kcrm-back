from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import EconomicYear

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'user', 'economic_year']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.economic_year.name}"

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=50, blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'user', 'economic_year']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.category.name}"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_level