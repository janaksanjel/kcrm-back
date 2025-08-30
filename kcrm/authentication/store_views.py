from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StoreConfig

def get_owner_user(request):
    """Helper function to get the owner user (shop owner for staff, or user itself)"""
    try:
        from staff.models import Staff
        staff = Staff.objects.get(user=request.user)
        return staff.shop_owner
    except Staff.DoesNotExist:
        return request.user

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def store_config(request):
    owner_user = get_owner_user(request)
    config, created = StoreConfig.objects.get_or_create(user=owner_user)
    
    if request.method == 'GET':
        return Response({
            'success': True,
            'data': {
                'store_url': config.store_url or '',
                'store_shortcode': config.store_shortcode or '',
                'owner_id': config.user.id
            }
        })
    
    elif request.method == 'PUT':
        store_url = request.data.get('store_url', '').strip()
        store_shortcode = request.data.get('store_shortcode', '').strip()
        
        if not store_url or not store_shortcode:
            return Response({
                'success': False,
                'message': 'Store URL and shortcode are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config.store_url = store_url
            config.store_shortcode = store_shortcode
            config.save()
            
            return Response({
                'success': True,
                'message': 'Store configuration updated successfully'
            })
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to update store configuration'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PATCH':
        store_url = request.data.get('store_url')
        store_shortcode = request.data.get('store_shortcode')
        
        try:
            if store_url is not None:
                config.store_url = store_url.strip()
            if store_shortcode is not None:
                config.store_shortcode = store_shortcode.strip()
            config.save()
            
            return Response({
                'success': True,
                'message': 'Store configuration updated successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to update store configuration'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            config.delete()
            return Response({
                'success': True,
                'message': 'Store configuration deleted successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to delete store configuration'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_availability(request):
    owner_user = get_owner_user(request)
    value = request.data.get('value', '').strip()
    field_type = request.data.get('type', 'username')  # 'username' or 'url'
    
    if not value:
        return Response({
            'success': False,
            'available': False,
            'message': f'{field_type.title()} is required'
        })
    
    # Check availability based on field type
    if field_type == 'url':
        exists = StoreConfig.objects.filter(
            store_url=value
        ).exclude(user=owner_user).exists()
        message = 'URL available' if not exists else 'URL already taken'
    else:
        exists = StoreConfig.objects.filter(
            store_shortcode=value
        ).exclude(user=owner_user).exists()
        message = 'Shortcode available' if not exists else 'Shortcode already taken'
    
    return Response({
        'success': True,
        'available': not exists,
        'message': message
    })