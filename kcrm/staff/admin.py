from django.contrib import admin
from .models import Role, Staff

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji', 'staff_count', 'created_date']
    search_fields = ['name', 'description']
    list_filter = ['created_date']

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'employee_id', 'is_active', 'hire_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    list_filter = ['role', 'is_active', 'hire_date']