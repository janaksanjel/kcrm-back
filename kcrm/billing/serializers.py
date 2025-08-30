from rest_framework import serializers
from .models import Customer, Sale, SaleItem, MenuCategory, MenuItem, MenuIngredient, KitchenOrder, KitchenOrderItem
from inventory.models import Stock
from staff.models import Staff

def get_owner_user_from_context(context):
    """Get the shop owner user for staff or return the user itself for shop owners"""
    request = context.get('request')
    if not request:
        return None
    
    if request.user.role == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            return staff.shop_owner
        except Staff.DoesNotExist:
            return request.user
    return request.user

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        owner_user = get_owner_user_from_context(self.context)
        if owner_user:
            from authentication.models import EconomicYear
            active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
            if active_year:
                validated_data['user'] = owner_user
                validated_data['economic_year'] = active_year
        return super().create(validated_data)

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
    payment_method = serializers.ChoiceField(choices=['cash', 'card', 'upi', 'credit', 'qr'], required=False)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    credit_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    points_earned = serializers.IntegerField(default=0)
    mode = serializers.CharField(default='regular')
    table_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    table_name = serializers.CharField(required=False, allow_blank=True)
    chair_ids = serializers.ListField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        owner_user = get_owner_user_from_context(self.context)
        if owner_user:
            from authentication.models import EconomicYear
            active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
            if active_year:
                validated_data['user'] = owner_user
                validated_data['economic_year'] = active_year
        return super().create(validated_data)

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        owner_user = get_owner_user_from_context(self.context)
        if owner_user:
            from authentication.models import EconomicYear
            active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
            if active_year:
                validated_data['user'] = owner_user
                validated_data['economic_year'] = active_year
        return super().create(validated_data)

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

class KitchenOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitchenOrderItem
        fields = '__all__'

class KitchenOrderSerializer(serializers.ModelSerializer):
    items = KitchenOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = KitchenOrder
        fields = '__all__'
        read_only_fields = ('user', 'economic_year', 'created_at', 'updated_at')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add fallback for empty table names using table_id if available
        if not data.get('table_name') or data.get('table_name').strip() == '' or 'Unknown Location - Unknown Table' in data.get('table_name', ''):
            if data.get('table_id'):
                data['table_name'] = f'Table {data.get("table_id")}'
            else:
                data['table_name'] = f'Order #{instance.id}'
        return data