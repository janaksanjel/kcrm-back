from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, ShopOwnerFeatures

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'shop_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            shop_name=validated_data.get('shop_name', ''),
            role='shop_owner'
        )
        ShopOwnerFeatures.objects.create(user=user)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField()  # Changed to CharField to accept both email and username
    password = serializers.CharField()

    def validate(self, attrs):
        email_or_username = attrs.get('email')
        password = attrs.get('password')

        if email_or_username and password:
            # Try to authenticate with email first
            user = authenticate(username=email_or_username, password=password)
            
            # If email authentication fails, try to find user by email and authenticate with username
            if not user and '@' in email_or_username:
                try:
                    user_obj = User.objects.get(email=email_or_username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if not user:
                raise serializers.ValidationError({"non_field_errors": "Invalid email/username or password"})
            if not user.is_active:
                raise serializers.ValidationError({"non_field_errors": "Account is disabled"})
            attrs['user'] = user
        return attrs

class SuperAdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, attrs):
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})
        
        # Check if username already exists
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists"})
        
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['username'],
            last_name='Admin',
            role='super_admin',
            is_staff=True,
            is_superuser=True
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'role', 'shop_name', 'features')

    def get_features(self, obj):
        if hasattr(obj, 'features'):
            return {
                'dashboard': obj.features.dashboard,
                'inventory': obj.features.inventory,
                'billing': obj.features.billing,
                'udhaar': obj.features.udhaar,
                'expenses': obj.features.expenses,
                'reports': obj.features.reports,
            }
        return None