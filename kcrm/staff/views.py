from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Role, Staff
from .serializers import RoleSerializer, StaffSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('-created_date')
    serializer_class = RoleSerializer

    def get_queryset(self):
        queryset = Role.objects.all().order_by('-created_date')
        mode = self.request.query_params.get('mode')
        if mode:
            queryset = queryset.filter(mode=mode)
        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        mode = request.query_params.get('mode')
        if mode:
            total_roles = Role.objects.filter(mode=mode).count()
            total_staff = Staff.objects.filter(role__mode=mode).count()
            active_staff = Staff.objects.filter(role__mode=mode, is_active=True).count()
        else:
            total_roles = Role.objects.count()
            total_staff = Staff.objects.count()
            active_staff = Staff.objects.filter(is_active=True).count()
        
        return Response({
            'total_roles': total_roles,
            'total_staff': total_staff,
            'active_staff': active_staff
        })

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all().order_by('-created_date')
    serializer_class = StaffSerializer

    def get_queryset(self):
        queryset = Staff.objects.filter(shop_owner=self.request.user).order_by('-created_date')
        mode = self.request.query_params.get('mode')
        if mode:
            queryset = queryset.filter(mode=mode)
        return queryset

    def perform_create(self, serializer):
        mode = self.request.data.get('mode', 'kirana')
        salary = self.request.data.get('salary')
        
        save_kwargs = {
            'shop_owner': self.request.user,
            'mode': mode,
            'restaurant_id': getattr(self.request.user, 'restaurant_id', None),
            'restaurant_name': getattr(self.request.user, 'shop_name', '')
        }
        
        if salary:
            save_kwargs['salary'] = salary
            
        serializer.save(**save_kwargs)

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        role_id = request.query_params.get('role_id')
        if role_id:
            staff = Staff.objects.filter(role_id=role_id, is_active=True, shop_owner=request.user)
            serializer = self.get_serializer(staff, many=True)
            return Response(serializer.data)
        return Response({'error': 'role_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def view_credentials(self, request, pk=None):
        from authentication.models import StoreConfig
        
        staff = self.get_object()
        if staff.shop_owner != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Split username to get shortcode and user parts
        full_username = staff.user.username
        if '.' in full_username:
            shortcode, username = full_username.split('.', 1)
        else:
            # Fallback for old usernames without shortcode
            try:
                store_config = StoreConfig.objects.get(user=request.user)
                shortcode = store_config.store_shortcode or 'shop'
            except StoreConfig.DoesNotExist:
                shortcode = 'shop'
            username = full_username
        
        return Response({
            'id': staff.id,
            'username': username,
            'shortcode': shortcode,
            'password': staff.user.unhashed_password or 'Password not available'
        })
    
    @action(detail=True, methods=['post'])
    def update_password(self, request, pk=None):
        import random
        import string
        
        staff = self.get_object()
        if staff.shop_owner != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get new password from request or generate one
        new_password = request.data.get('new_password')
        if not new_password:
            new_password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))
        
        # Update user password
        staff.user.set_password(new_password)
        staff.user.unhashed_password = new_password
        staff.user.save()
        
        return Response({
            'success': True,
            'new_password': new_password,
            'message': 'Password updated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def generate_username(self, request, pk=None):
        import random
        import string
        import re
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        staff = self.get_object()
        if staff.shop_owner != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Generate new username
        first_name = staff.user.first_name
        last_name = staff.user.last_name
        base = first_name[:3].lower() + last_name[:3].lower()
        base = re.sub(r'[^a-z]', '', base)[:6]
        
        if len(base) < 3:
            base = staff.user.email.split('@')[0][:3].lower()
        
        # Add random digits
        new_username = base + ''.join(random.choices(string.digits, k=3))
        
        # Ensure uniqueness
        while User.objects.filter(username=new_username).exists():
            new_username = base + ''.join(random.choices(string.digits, k=3))
        
        # Update username
        staff.user.username = new_username
        staff.user.save()
        
        return Response({
            'success': True,
            'new_username': new_username,
            'message': 'Username updated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        staff = self.get_object()
        if staff.shop_owner != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Toggle the is_active status
        staff.is_active = not staff.is_active
        staff.save()
        
        return Response({
            'success': True,
            'is_active': staff.is_active,
            'message': f'Staff member {"activated" if staff.is_active else "deactivated"} successfully'
        })
    
    @action(detail=True, methods=['get'])
    def get_staff_permissions(self, request, pk=None):
        from .models import Permission
        
        staff = self.get_object()
        if staff.shop_owner != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            permission = Permission.objects.get(staff=staff)
            return Response({
                'permissions': permission.permissions_data,
                'mode': staff.mode
            })
        except Permission.DoesNotExist:
            return Response({
                'permissions': {},
                'mode': staff.mode
            })
    
    @action(detail=True, methods=['post'])
    def update_permissions(self, request, pk=None):
        from .models import Permission
        
        staff = self.get_object()
        if staff.shop_owner != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        permissions_data = request.data.get('permissions', {})
        
        permission, created = Permission.objects.get_or_create(
            staff=staff,
            defaults={'permissions_data': permissions_data}
        )
        
        if not created:
            permission.permissions_data = permissions_data
            permission.save()
        
        return Response({
            'success': True,
            'message': 'Permissions updated successfully'
        })