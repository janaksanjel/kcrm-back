from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import EconomicYear

User = get_user_model()

class Category(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership')
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='kirana')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'user', 'economic_year', 'mode']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.economic_year.name}"

class Supplier(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership')
    ]
    
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=50)
    address = models.TextField()
    categories = models.JSONField(default=list, blank=True)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='kirana')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'user', 'economic_year', 'mode']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"

class Stock(models.Model):
    STATUS_CHOICES = [
        ('Good', 'Good'),
        ('Low', 'Low'),
        ('Critical', 'Critical'),
        ('Overstock', 'Overstock')
    ]
    
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership')
    ]
    
    product_name = models.CharField(max_length=200)
    current_stock = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, default='kg')
    min_stock = models.IntegerField(default=0)
    max_stock = models.IntegerField(default=100)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Good')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='kirana')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product_name', 'user', 'economic_year', 'mode']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.product_name} - {self.current_stock} {self.unit}"
    
    def update_status(self):
        if self.current_stock <= 0:
            self.status = 'Critical'
        elif self.current_stock <= self.min_stock:
            self.status = 'Low'
        elif self.current_stock >= self.max_stock:
            self.status = 'Overstock'
        else:
            self.status = 'Good'
        self.save()

class Purchase(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial')
    ]
    
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership')
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='purchases')
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    unit = models.CharField(max_length=20, default='kg')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    auto_add_stock = models.BooleanField(default=False)
    isTransferredStock = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='kirana')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey(EconomicYear, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date', '-created_at']

    def __str__(self):
        return f"{self.product_name} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.quantity * self.unit_price
        
        # Calculate selling price if not set
        if not self.selling_price:
            from decimal import Decimal
            from billing.models import ProfitPercentage
            try:
                profit = ProfitPercentage.objects.first()
                profit_percentage = Decimal(str(profit.percentage)) if profit else Decimal('20.0')
                self.selling_price = self.unit_price * (Decimal('1') + profit_percentage / Decimal('100'))
            except:
                self.selling_price = self.unit_price * Decimal('1.2')  # Default 20% profit
        
        super().save(*args, **kwargs)
        
        # Auto add to stock if enabled
        if self.auto_add_stock:
            stock, created = Stock.objects.get_or_create(
                product_name=self.product_name,
                user=self.user,
                economic_year=self.economic_year,
                mode=self.mode,
                defaults={'current_stock': 0, 'unit': self.unit}
            )
            stock.current_stock += self.quantity
            stock.update_status()
        
        # Update supplier total payments if paid
        if self.payment_status == 'paid':
            self.supplier.total_payments = self.supplier.purchases.filter(payment_status='paid').aggregate(
                total=models.Sum('total_amount')
            )['total'] or 0
            self.supplier.save()