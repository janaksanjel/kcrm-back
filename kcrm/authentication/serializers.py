from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from .models import User, ShopOwnerFeatures, UserSession, EconomicYear, NotificationSettings, SecuritySettings, SecurityActivity

def get_owner_user(request):
    """Helper function to get the owner user (shop owner for staff, or user itself)"""
    try:
        from staff.models import Staff
        staff = Staff.objects.get(user=request.user)
        return staff.shop_owner
    except Staff.DoesNotExist:
        return request.user

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'shop_name', 'selected_modes')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
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
            phone=validated_data.get('phone', ''),
            shop_name=validated_data.get('shop_name', ''),
            role='shop_owner',
            is_approved=False,  # Set as pending by default
            selected_modes=validated_data.get('selected_modes', [])
        )
        ShopOwnerFeatures.objects.create(user=user)
        NotificationSettings.objects.create(user=user)
        SecuritySettings.objects.create(user=user)
        return user

class SuperAdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, attrs):
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})
        
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
        NotificationSettings.objects.create(user=user)
        SecuritySettings.objects.create(user=user)
        return user

class KitchenUserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ('username', 'password')

    def validate(self, attrs):
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists"})
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        owner_user = get_owner_user(request) if request else None
        restaurant_id = owner_user.id if owner_user else None
        
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['username'],
            last_name='Kitchen',
            role='kitchen_user',
            restaurant_id=restaurant_id
        )
        # Store unhashed password for kitchen users
        user.unhashed_password = validated_data['password']
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email_or_username = attrs.get('email')
        password = attrs.get('password')

        if email_or_username and password:
            user = authenticate(username=email_or_username, password=password)
            
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
            if user.role == 'shop_owner':
                # Check if user has a rejected status
                try:
                    from superadmin.models import ShopOwnerRequest
                    shop_request = ShopOwnerRequest.objects.get(user=user)
                    if shop_request.status == 'rejected':
                        raise serializers.ValidationError({"non_field_errors": "Your account has been rejected. Please contact support."})
                except ShopOwnerRequest.DoesNotExist:
                    pass
                
                # Check if user is not approved (pending)
                if not getattr(user, 'is_approved', True):
                    raise serializers.ValidationError({"non_field_errors": "Your account is pending approval. Please wait for admin approval."})
            
            attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    restaurant_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'role', 'shop_name', 'restaurant_name', 'features')

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
    
    def get_restaurant_name(self, obj):
        if obj.role == 'kitchen_user' and obj.restaurant_id:
            try:
                restaurant_owner = User.objects.get(id=obj.restaurant_id)
                return restaurant_owner.shop_name
            except User.DoesNotExist:
                return None
        return obj.shop_name

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'shop_name')

class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not check_password(value, user.password):
            raise serializers.ValidationError("Current password is incorrect")
        return value

class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ('id', 'device_info', 'ip_address', 'location', 'is_current', 'created_at', 'last_activity')

class EconomicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = EconomicYear
        fields = ('id', 'name', 'start_date', 'end_date', 'status', 'is_active', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context.get('owner_user', self.context['request'].user)
        return super().create(validated_data)

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = ('low_stock_alerts', 'payment_reminders', 'daily_reports', 'system_updates', 'login_notifications')

class SecuritySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecuritySettings
        fields = ('two_factor_enabled', 'login_notifications')

class SecurityActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityActivity
        fields = ('id', 'activity_type', 'description', 'ip_address', 'device_info', 'created_at')