from rest_framework import serializers
from .models import Customer, Sale, SaleItem, MenuCategory, MenuItem, MenuIngredient

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = '__all__'

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = ('cashier', 'economic_year', 'created_at', 'updated_at')

class POSCreateSerializer(serializers.Serializer):
    items = serializers.ListField()
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    payment_method = serializers.ChoiceField(choices=['cash', 'card', 'upi'])
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    points_earned = serializers.IntegerField(default=0)
    mode = serializers.CharField(default='regular')

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')

class MenuIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.product_name', read_only=True)
    
    class Meta:
        model = MenuIngredient
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

# Table System Serializers
class FloorSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField(max_length=100)
    expanded = serializers.BooleanField(default=True)

class RoomSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField(max_length=100)
    floor_id = serializers.CharField()
    expanded = serializers.BooleanField(default=True)

class ChairSerializer(serializers.Serializer):
    id = serializers.CharField()
    position = serializers.IntegerField()
    occupied = serializers.BooleanField(default=False)

class TableSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField(max_length=100)
    room_id = serializers.CharField()
    status = serializers.ChoiceField(choices=['available', 'occupied', 'reserved'], default='available')
    position_x = serializers.FloatField()
    position_y = serializers.FloatField()
    chairs = ChairSerializer(many=True)