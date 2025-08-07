from rest_framework import serializers
from .models import Customer, Sale, SaleItem, Invoice, InvoiceItem
from inventory.models import Stock

class CustomerSerializer(serializers.ModelSerializer):
    points = serializers.IntegerField(source='loyalty_points', read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'address', 'loyalty_points', 'points', 
                 'total_purchases', 'total_spent', 'status', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure numeric fields are properly formatted
        data['total_spent'] = float(instance.total_spent) if instance.total_spent else 0.0
        data['loyalty_points'] = int(instance.loyalty_points) if instance.loyalty_points else 0
        data['points'] = data['loyalty_points']
        data['total_purchases'] = int(instance.total_purchases) if instance.total_purchases else 0
        return data

class SaleItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source='unit_price', max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(source='total_price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SaleItem
        fields = ['product_name', 'quantity', 'price', 'total', 'unit']

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    sale_items = SaleItemSerializer(many=True, read_only=True, source='items')
    
    class Meta:
        model = Sale
        fields = '__all__'
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure both items and sale_items are available
        data['sale_items'] = data['items']
        return data

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_address = serializers.CharField(source='customer.address', read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'

class POSCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    items = serializers.ListField(child=serializers.DictField())
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = serializers.ChoiceField(choices=['cash', 'card', 'upi'])
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    points_earned = serializers.IntegerField(default=0)
    mode = serializers.ChoiceField(choices=['regular', 'kirana'], default='regular')

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'product_name', 'current_stock', 'unit', 'min_stock', 
                 'max_stock', 'status', 'created_at', 'updated_at']

