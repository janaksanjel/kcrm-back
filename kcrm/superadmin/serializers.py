from rest_framework import serializers
from .models import ShopOwnerPermissions
from staff.models import Permission, Staff

class UserPermissionSerializer(serializers.Serializer):
    """Unified serializer for all user permissions"""
    user_id = serializers.IntegerField()
    user_role = serializers.CharField()
    permissions = serializers.JSONField()
    active_modes = serializers.ListField()
    
    def to_representation(self, instance):
        user = instance
        data = {
            'user_id': user.id,
            'user_role': user.role,
            'permissions': {},
            'active_modes': []
        }
        
        if user.role == 'super_admin':
            # Super admin has all permissions
            data['permissions'] = {
                'inventory': True,
                'billing': True,
                'staff': True,
                'reports': True,
                'settings': True
            }
            data['active_modes'] = ['kirana', 'restaurant', 'dealership']
            
        elif user.role == 'shop_owner':
            # Get ShopOwnerPermissions
            shop_permissions = ShopOwnerPermissions.objects.filter(user=user, is_active=True)
            permissions_dict = {}
            active_modes = []
            
            for perm in shop_permissions:
                permissions_dict[perm.mode] = perm.permissions
                active_modes.append(perm.mode)
            
            data['permissions'] = permissions_dict
            data['active_modes'] = active_modes
            
        elif user.role == 'staff':
            # Get Staff permissions - return structure identical to shop owners
            try:
                staff = Staff.objects.get(user=user)
                staff_permission = Permission.objects.get(staff=staff)
                permissions_data = staff_permission.permissions_data
                
                # Transform staff permissions to match shop owner structure exactly
                transformed_permissions = {}
                
                # Add _enabled flags for each section
                for key, value in permissions_data.items():
                    if isinstance(value, dict):
                        # For nested permissions (like inventory, billing)
                        transformed_permissions[key] = value
                        # Add _enabled flag - true if any sub-permission is true
                        transformed_permissions[key + '_enabled'] = any(v for v in value.values() if isinstance(v, bool) and v)
                    elif isinstance(value, bool):
                        # For direct boolean permissions
                        transformed_permissions[key] = value
                        transformed_permissions[key + '_enabled'] = value
                
                # Wrap in mode structure like shop owners
                mode_permissions = {}
                mode = staff.mode if staff.mode else 'kirana'
                mode_permissions[mode] = transformed_permissions
                
                data['permissions'] = mode_permissions
                data['active_modes'] = [mode]
            except (Staff.DoesNotExist, Permission.DoesNotExist):
                data['permissions'] = {}
                data['active_modes'] = []
        
        return data