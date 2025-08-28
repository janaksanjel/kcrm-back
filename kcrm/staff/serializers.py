from rest_framework import serializers
from .models import Role, UserRole, Staff
from authentication.models import EconomicYear, User

class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'mode', 'permissions', 'is_active', 'user_count', 'created_at', 'updated_at']
        read_only_fields = ['user', 'economic_year', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        return Staff.objects.filter(role=obj, status='active').count()
    
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

class StaffSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    password = serializers.CharField(read_only=True)
    
    class Meta:
        model = Staff
        fields = ['id', 'name', 'email', 'phone', 'role', 'role_name', 'username', 'password', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'economic_year', 'user', 'auto_password', 'created_at', 'updated_at']
    
    def get_role_name(self, obj):
        return obj.role.name if obj.role else 'No Role'
    
    def create(self, validated_data):
        request = self.context['request']
        
        try:
            active_year = EconomicYear.objects.get(user=request.user, is_active=True)
        except EconomicYear.DoesNotExist:
            raise serializers.ValidationError("No active economic year found")
        
        # Generate username from email
        email = validated_data['email']
        username = email.split('@')[0]
        
        # Ensure unique username
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        # Generate password
        staff = Staff()
        password = staff.generate_password()
        
        # Create user account
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=validated_data['name'].split()[0],
            last_name=' '.join(validated_data['name'].split()[1:]) if len(validated_data['name'].split()) > 1 else '',
            phone=validated_data.get('phone', ''),
            role='staff'
        )
        
        # Create staff record
        validated_data['user'] = user
        validated_data['created_by'] = request.user
        validated_data['economic_year'] = active_year
        validated_data['auto_password'] = password
        
        staff = Staff.objects.create(**validated_data)
        return staff
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Only show password during creation
        if hasattr(self, '_password_shown'):
            data['password'] = instance.auto_password
        return data

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