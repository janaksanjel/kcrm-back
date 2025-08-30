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

    class Meta:
        model = Staff
        fields = ['id', 'user', 'role', 'role_name', 'role_emoji', 'employee_id', 'phone', 'address', 'hire_date', 'is_active', 'created_date']