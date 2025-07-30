from rest_framework import serializers
from .models import Category, Supplier, Purchase

class CategorySerializer(serializers.ModelSerializer):
    purchases_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'purchases_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_purchases_count(self, obj):
        return obj.purchases.count()
    
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

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact', 'address', 'categories', 'total_payments', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        from authentication.models import EconomicYear
        active_year = EconomicYear.objects.filter(user=user, is_active=True).first()
        if not active_year:
            raise serializers.ValidationError("No active economic year found")
        
        validated_data['user'] = user
        validated_data['economic_year'] = active_year
        return super().create(validated_data)

class PurchaseSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Purchase
        fields = ['id', 'supplier', 'supplier_name', 'category', 'category_name', 'product_name', 
                 'quantity', 'unit_price', 'total_amount', 'purchase_date', 'payment_status', 
                 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        from authentication.models import EconomicYear
        active_year = EconomicYear.objects.filter(user=user, is_active=True).first()
        if not active_year:
            raise serializers.ValidationError("No active economic year found")
        
        validated_data['user'] = user
        validated_data['economic_year'] = active_year
        return super().create(validated_data)