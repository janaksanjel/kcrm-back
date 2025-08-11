from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    loyalty_points = models.IntegerField(default=0)
    total_purchases = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['phone', 'user', 'economic_year']

    def __str__(self):
        return self.name

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]
    
    MODE_CHOICES = [
        ('regular', 'Regular'),
        ('kirana', 'Kirana'),
    ]
    
    sale_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    points_earned = models.IntegerField(default=0)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='regular')
    cashier = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sale {self.sale_number}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.product_name} - {self.quantity} {self.unit}"

class MenuCategory(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'mode', 'user', 'economic_year']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.mode})"

class MenuItem(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='menu_items')
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    available = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.category.name}"

class MenuIngredient(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey('inventory.Stock', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['menu_item', 'ingredient']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.ingredient.product_name} ({self.quantity})"

class ProfitPercentage(models.Model):
    MODE_CHOICES = [
        ('kirana', 'Kirana'),
        ('restaurant', 'Restaurant'),
        ('dealership', 'Dealership'),
    ]
    
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE, null=True, blank=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        eco_year_name = self.economic_year.name if self.economic_year else 'No Year'
        mode_name = self.mode or 'No Mode'
        return f"Profit: {self.percentage}% ({mode_name} - {eco_year_name})"

class Floor(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    expanded = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'user', 'economic_year']
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Room(models.Model):
    name = models.CharField(max_length=100)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    expanded = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'floor', 'user', 'economic_year']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.floor.name} - {self.name}"

class Table(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
    ]
    
    name = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tables')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    position_x = models.FloatField(default=100)
    position_y = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'room', 'user', 'economic_year']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.room.floor.name} - {self.room.name} - {self.name}"

class Chair(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='chairs')
    position = models.IntegerField()
    occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['table', 'position']
        ordering = ['position']
    
    def __str__(self):
        return f"{self.table.name} - Chair {self.position}"

class KitchenOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('completed', 'Completed'),
    ]
    
    table_id = models.CharField(max_length=50)
    table_name = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chair_ids = models.JSONField(default=list, blank=True)  # Add this field
    economic_year = models.ForeignKey('authentication.EconomicYear', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.id} - {self.table_name} ({self.status})"

class KitchenOrderItem(models.Model):
    order = models.ForeignKey(KitchenOrder, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} x{self.quantity}"

