from rest_framework import serializers
from .models import Role, Staff
from django.contrib.auth import get_user_model

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    staff_count = serializers.ReadOnlyField()
    created_date = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'emoji', 'color', 'mode', 'staff_count', 'created_date']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_emoji = serializers.CharField(source='role.emoji', read_only=True)
    shop_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # User creation fields
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = Staff
        fields = ['id', 'user', 'role', 'role_name', 'role_emoji', 'shop_owner', 'mode', 'restaurant_id', 'restaurant_name', 'employee_id', 'phone', 'address', 'hire_date', 'salary', 'is_active', 'created_date', 'first_name', 'last_name', 'email']
    
    def create(self, validated_data):
        import random
        import string
        import re
        from authentication.models import StoreConfig
        
        # Extract user data
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        email = validated_data.pop('email')
        
        # Get store shortcode from request context
        request = self.context.get('request')
        try:
            store_config = StoreConfig.objects.get(user=request.user)
            store_shortcode = store_config.store_shortcode or 'shop'
        except (StoreConfig.DoesNotExist, AttributeError):
            store_shortcode = 'shop'
        
        # Generate user code
        base = first_name[:3].lower() + last_name[:3].lower()
        base = re.sub(r'[^a-z]', '', base)[:6]
        
        # Ensure minimum length
        if len(base) < 3:
            base = email.split('@')[0][:3].lower()
        
        # Add random digits to make it unique
        user_code = base + ''.join(random.choices(string.digits, k=3))
        
        # Create full username with shortcode prefix
        full_username = f"{store_shortcode}.{user_code}"
        
        # Ensure uniqueness
        while User.objects.filter(username=full_username).exists():
            user_code = base + ''.join(random.choices(string.digits, k=3))
            full_username = f"{store_shortcode}.{user_code}"
        
        # Generate random password
        password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))
        
        # Create user
        user = User.objects.create_user(
            username=full_username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='staff',
            unhashed_password=password
        )
        
        # Set restaurant_id to shop_owner's ID
        validated_data['restaurant_id'] = request.user.id
        
        # Create staff with the user
        staff = Staff.objects.create(user=user, **validated_data)
        return staff