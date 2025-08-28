from rest_framework import serializers
from .models import Role, UserRole
from authentication.models import EconomicYear

class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'mode', 'permissions', 'is_active', 'user_count', 'created_at', 'updated_at']
        read_only_fields = ['user', 'economic_year', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        return obj.userrole_set.filter(is_active=True).count()
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Get active economic year
        try:
            active_year = EconomicYear.objects.get(user=user, is_active=True)
        except EconomicYear.DoesNotExist:
            raise serializers.ValidationError("No active economic year found")
        
        validated_data['user'] = user
        validated_data['economic_year'] = active_year
        
        return Role.objects.create(**validated_data)

class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.IntegerField(write_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_name', 'role', 'role_id', 'is_active', 'assigned_at']
        read_only_fields = ['assigned_by', 'assigned_at']
    
    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)