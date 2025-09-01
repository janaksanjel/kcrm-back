from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import ShopOwnerRequest, ShopOwnerPermissions

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_shop_owners(request):
    if request.user.role != 'super_admin':
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)
    
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'all':
        users = User.objects.filter(role='shop_owner')
    else:
        users = User.objects.filter(role='shop_owner', shop_request__status=status_filter)
    
    data = []
    for user in users:
        request_obj = getattr(user, 'shop_request', None)
        data.append({
            'id': user.id,
            'shopName': user.shop_name,
            'ownerName': f"{user.first_name} {user.last_name}",
            'phone': user.phone,
            'email': user.email,
            'submittedDate': user.created_at.strftime('%Y-%m-%d'),
            'status': request_obj.status if request_obj else 'pending'
        })
    
    return Response({'success': True, 'data': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_shop_owner(request, user_id):
    if request.user.role != 'super_admin':
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        user = User.objects.get(id=user_id, role='shop_owner')
        shop_request, created = ShopOwnerRequest.objects.get_or_create(user=user)
        
        shop_request.status = 'approved'
        shop_request.approved_by = request.user
        shop_request.approved_at = timezone.now()
        shop_request.save()
        
        user.is_verified = True
        user.save()
        
        return Response({'success': True, 'message': 'Shop owner approved successfully'})
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_shop_owner(request, user_id):
    if request.user.role != 'super_admin':
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        user = User.objects.get(id=user_id, role='shop_owner')
        shop_request, created = ShopOwnerRequest.objects.get_or_create(user=user)
        
        shop_request.status = 'rejected'
        shop_request.rejected_at = timezone.now()
        shop_request.save()
        
        return Response({'success': True, 'message': 'Shop owner rejected successfully'})
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=404)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_shop_owner(request, user_id):
    if request.user.role != 'super_admin':
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        user = User.objects.get(id=user_id, role='shop_owner')
        user.delete()
        return Response({'success': True, 'message': 'Shop owner deleted successfully'})
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request, user_id):
    if request.user.role != 'super_admin':
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        user = User.objects.get(id=user_id, role='shop_owner')
        new_password = request.data.get('password')
        
        if not new_password:
            return Response({'success': False, 'message': 'Password is required'}, status=400)
        
        user.password = make_password(new_password)
        user.save()
        
        return Response({'success': True, 'message': 'Password changed successfully'})
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=404)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_permissions(request, user_id):
    if request.user.role != 'super_admin':
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        user = User.objects.get(id=user_id, role='shop_owner')
        
        if request.method == 'GET':
            permissions = ShopOwnerPermissions.objects.filter(user=user)
            data = {}
            for perm in permissions:
                data[perm.mode] = perm.permissions
            return Response({'success': True, 'data': data})
        
        elif request.method == 'POST':
            modes = request.data.get('modes', [])
            permissions_data = request.data.get('permissions', {})
            
            # Clear existing permissions
            ShopOwnerPermissions.objects.filter(user=user).delete()
            
            # Create new permissions
            for mode in modes:
                if mode in permissions_data:
                    ShopOwnerPermissions.objects.create(
                        user=user,
                        mode=mode,
                        permissions=permissions_data[mode]
                    )
            
            return Response({'success': True, 'message': 'Permissions updated successfully'})
            
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=404)