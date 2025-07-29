from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ShopOwnerFeatures

class ShopOwnerFeaturesInline(admin.StackedInline):
    model = ShopOwnerFeatures
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (ShopOwnerFeaturesInline,)
    list_display = ('email', 'first_name', 'last_name', 'phone', 'role', 'shop_name', 'is_verified')
    list_filter = ('role', 'is_verified', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'shop_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role', 'shop_name', 'is_verified')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(ShopOwnerFeatures)