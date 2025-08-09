from rest_framework import serializers
from .models import Customer, Sale, SaleItem, ProfitPercentage, MenuCategory, MenuItem, MenuIngredient

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

class MenuCategorySerializer(serializers.ModelSerializer):
    menu_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description', 'mode', 'is_active', 'menu_items_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_menu_items_count(self, obj):
        return obj.menu_items.count()

class MenuIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.product_name', read_only=True)
    ingredient_id = serializers.IntegerField(source='ingredient.id', read_only=True)
    ingredient_unit = serializers.CharField(source='ingredient.unit', read_only=True)
    
    class Meta:
        model = MenuIngredient
        fields = ['id', 'ingredient_id', 'ingredient_name', 'ingredient_unit', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'category_name', 'image', 'image_url', 'available', 'stock', 'mode', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class ProfitPercentageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfitPercentage
        fields = ['id', 'percentage', 'economic_year', 'mode', 'updated_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'updated_by', 'created_at', 'updated_at']



