from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'products_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.count()
    
    def create(self, validated_data):
        user = self.context['request'].user
        # Get active economic year
        from authentication.models import EconomicYear
        active_year = EconomicYear.objects.filter(user=user, is_active=True).first()
        if not active_year:
            raise serializers.ValidationError("No active economic year found")
        
        validated_data['user'] = user
        validated_data['economic_year'] = active_year
        return super().create(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category', 'category_name', 'sku', 'barcode', 
                 'cost_price', 'selling_price', 'stock_quantity', 'min_stock_level', 
                 'is_active', 'is_low_stock', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        # Get active economic year
        from authentication.models import EconomicYear
        active_year = EconomicYear.objects.filter(user=user, is_active=True).first()
        if not active_year:
            raise serializers.ValidationError("No active economic year found")
        
        validated_data['user'] = user
        validated_data['economic_year'] = active_year
        return super().create(validated_data)