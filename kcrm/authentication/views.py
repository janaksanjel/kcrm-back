from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone
import uuid
import hashlib
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer, SuperAdminRegistrationSerializer,
    KitchenUserRegistrationSerializer, ProfileUpdateSerializer, PasswordChangeSerializer, UserSessionSerializer, EconomicYearSerializer,
    NotificationSettingsSerializer, SecuritySettingsSerializer, SecurityActivitySerializer
)
from .models import UserSession, EconomicYear, NotificationSettings, SecuritySettings, SecurityActivity, StoreConfig
from staff.models import Staff

User = get_user_model()

def get_owner_user(request):
    """Get the shop owner user for staff or return the user itself for shop owners"""
    if request.user.role == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            return staff.shop_owner
        except Staff.DoesNotExist:
            return request.user
    return request.user

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # For shop owners, don't create session or return tokens - they need approval
        if user.role == 'shop_owner':
            return Response({
                'success': True,
                'message': 'Registration successful. Your account is pending approval.',
            }, status=status.HTTP_201_CREATED)
        
        # For other user types (super_admin, etc.), proceed with normal login
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        
        # Create session record for approved users
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        device_info = parse_user_agent(user_agent)
        
        # Generate unique session key
        unique_string = f"{user.id}-{timezone.now().timestamp()}-{uuid.uuid4()}"
        session_key = hashlib.md5(unique_string.encode()).hexdigest()[:40]
        
        UserSession.objects.create(
            user=user,
            session_key=session_key,
            device_info=device_info,
            ip_address=ip_address,
            location=get_location_from_ip(ip_address),
            is_current=True
        )
        
        return Response({
            'success': True,
            'message': 'Registration successful',
            'user': user_data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        
        # Create session record
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # Parse device info from user agent
        device_info = parse_user_agent(user_agent)
        
        # Generate unique session key
        unique_string = f"{user.id}-{timezone.now().timestamp()}-{uuid.uuid4()}"
        session_key = hashlib.md5(unique_string.encode()).hexdigest()[:40]
        
        # Mark all other sessions as not current
        UserSession.objects.filter(user=user).update(is_current=False)
        
        # Create new session
        UserSession.objects.create(
            user=user,
            session_key=session_key,
            device_info=device_info,
            ip_address=ip_address,
            location=get_location_from_ip(ip_address),
            is_current=True
        )
        
        # Log security activity
        log_security_activity(user, 'login', f'Successful login from {device_info}', request)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': user_data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Login failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

def parse_user_agent(user_agent):
    """Parse user agent to extract device and browser info"""
    if 'Chrome' in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent:
        browser = 'Safari'
    elif 'Edge' in user_agent:
        browser = 'Edge'
    else:
        browser = 'Unknown Browser'
    
    if 'Windows' in user_agent:
        os = 'Windows'
    elif 'Mac' in user_agent:
        os = 'macOS'
    elif 'Linux' in user_agent:
        os = 'Linux'
    elif 'Android' in user_agent:
        os = 'Android'
    elif 'iOS' in user_agent:
        os = 'iOS'
    else:
        os = 'Unknown OS'
    
    return f'{browser} on {os}'

def get_location_from_ip(ip_address):
    """Get location from IP address (simplified)"""
    # For now, return a default location
    # In production, you could use a service like GeoIP
    if ip_address == '127.0.0.1' or ip_address.startswith('192.168'):
        return 'Local Network'
    return 'Unknown Location'

def log_security_activity(user, activity_type, description, request):
    """Log security activity"""
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
    if ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()
    
    device_info = parse_user_agent(user_agent)
    
    SecurityActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address,
        device_info=device_info
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def super_admin_register(request):
    serializer = SuperAdminRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        
        # Create session record for super admin
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        device_info = parse_user_agent(user_agent)
        
        # Generate unique session key
        unique_string = f"{user.id}-{timezone.now().timestamp()}-{uuid.uuid4()}"
        session_key = hashlib.md5(unique_string.encode()).hexdigest()[:40]
        
        UserSession.objects.create(
            user=user,
            session_key=session_key,
            device_info=device_info,
            ip_address=ip_address,
            location=get_location_from_ip(ip_address),
            is_current=True
        )
        
        return Response({
            'success': True,
            'message': 'Super admin registration successful',
            'user': user_data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Super admin registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        # Clean up current session record
        UserSession.objects.filter(
            user=request.user,
            is_current=True
        ).delete()
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({
            'success': False,
            'message': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user_data = UserSerializer(request.user).data
    owner_user = get_owner_user(request)
    
    # Add store name for all users
    user_data['store_name'] = owner_user.shop_name or 'N/A'
    
    # For staff users, show shop owner's shop name but keep staff's own phone
    if request.user.role == 'staff':
        user_data['shop_name'] = owner_user.shop_name or ''
        
        # Add staff role information
        try:
            staff = Staff.objects.get(user=request.user)
            user_data['staff_role'] = staff.role.name if staff.role else 'Staff'
            user_data['staff_role_emoji'] = staff.role.emoji if staff.role else '👤'
        except Staff.DoesNotExist:
            user_data['staff_role'] = 'Staff'
            user_data['staff_role_emoji'] = '👤'
    
    return Response({
        'success': True,
        'user': user_data
    }, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': UserSerializer(request.user).data
        })
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    print(f"Password change request data: {request.data}")
    print(f"User: {request.user}")
    
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    print(f"Serializer is valid: {serializer.is_valid()}")
    
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log security activity
        log_security_activity(user, 'password_change', 'Password changed successfully', request)
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })
    
    print(f"Serializer errors: {serializer.errors}")
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_password(request):
    # For security reasons, we don't actually return the password
    return Response({
        'success': True,
        'message': 'Password viewing is not allowed for security reasons'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sessions(request):
    sessions = UserSession.objects.filter(user=request.user).order_by('-last_activity')
    serializer = UserSessionSerializer(sessions, many=True)
    return Response({
        'success': True,
        'sessions': serializer.data
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def terminate_session(request, session_id):
    try:
        session = UserSession.objects.get(id=session_id, user=request.user)
        session.delete()
        return Response({
            'success': True,
            'message': 'Session terminated successfully'
        })
    except UserSession.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminate_all_sessions(request):
    UserSession.objects.filter(user=request.user, is_current=False).delete()
    return Response({
        'success': True,
        'message': 'All other sessions terminated successfully'
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def economic_years(request):
    owner_user = get_owner_user(request)
    if request.method == 'GET':
        years = EconomicYear.objects.filter(user=owner_user).order_by('-created_at')
        serializer = EconomicYearSerializer(years, many=True)
        return Response({
            'success': True,
            'economic_years': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = EconomicYearSerializer(data=request.data, context={'request': request, 'owner_user': owner_user})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Economic year created successfully',
                'economic_year': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_economic_year(request, year_id):
    try:
        owner_user = get_owner_user(request)
        year = EconomicYear.objects.get(id=year_id, user=owner_user)
        
        if request.method == 'PUT':
            serializer = EconomicYearSerializer(year, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Economic year updated successfully',
                    'economic_year': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            if year.is_active:
                return Response({
                    'success': False,
                    'message': 'Cannot delete active economic year'
                }, status=status.HTTP_400_BAD_REQUEST)
            year.delete()
            return Response({
                'success': True,
                'message': 'Economic year deleted successfully'
            })
            
    except EconomicYear.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Economic year not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_economic_year(request, year_id):
    try:
        owner_user = get_owner_user(request)
        year = EconomicYear.objects.get(id=year_id, user=owner_user)
        if year.is_active:
            year.is_active = False
        else:
            EconomicYear.objects.filter(user=owner_user).update(is_active=False)
            year.is_active = True
        year.save()
        return Response({
            'success': True,
            'message': 'Economic year status updated successfully'
        })
    except EconomicYear.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Economic year not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def header_economic_years(request):
    if request.user.role == 'kitchen_user' and request.user.restaurant_id:
        years = EconomicYear.objects.filter(user_id=request.user.restaurant_id).order_by('-created_at')
    else:
        owner_user = get_owner_user(request)
        years = EconomicYear.objects.filter(user=owner_user).order_by('-created_at')
    serializer = EconomicYearSerializer(years, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_settings(request):
    settings, created = NotificationSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = NotificationSettingsSerializer(settings)
        return Response({
            'success': True,
            'settings': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = NotificationSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Notification settings updated successfully',
                'settings': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def security_settings(request):
    settings, created = SecuritySettings.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = SecuritySettingsSerializer(settings)
        return Response({
            'success': True,
            'settings': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = SecuritySettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Security settings updated successfully',
                'settings': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_activity(request):
    activities = SecurityActivity.objects.filter(user=request.user)[:10]  # Last 10 activities
    serializer = SecurityActivitySerializer(activities, many=True)
    return Response({
        'success': True,
        'activities': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_kitchen_user(request):
    owner_user = get_owner_user(request)
    # Only shop owners and staff can create kitchen users
    if owner_user.role != 'shop_owner':
        return Response({
            'success': False,
            'message': 'Only shop owners can create kitchen users'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = KitchenUserRegistrationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.save()
        user_data = UserSerializer(user).data
        
        return Response({
            'success': True,
            'message': 'Kitchen user created successfully',
            'user': user_data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Kitchen user creation failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kitchen_users(request):
    owner_user = get_owner_user(request)
    # Only shop owners and staff can view kitchen users
    if owner_user.role != 'shop_owner':
        return Response({
            'success': False,
            'message': 'Only shop owners can view kitchen users'
        }, status=status.HTTP_403_FORBIDDEN)
    
    kitchen_users = User.objects.filter(role='kitchen_user', restaurant_id=owner_user.id)
    serializer = UserSerializer(kitchen_users, many=True)
    
    return Response({
        'success': True,
        'kitchen_users': serializer.data
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_kitchen_user(request, user_id):
    owner_user = get_owner_user(request)
    # Only shop owners and staff can delete kitchen users
    if owner_user.role != 'shop_owner':
        return Response({
            'success': False,
            'message': 'Only shop owners can delete kitchen users'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id, role='kitchen_user', restaurant_id=owner_user.id)
        user.delete()
        return Response({
            'success': True,
            'message': 'Kitchen user deleted successfully'
        })
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kitchen user not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kitchen_user_credentials(request, user_id):
    owner_user = get_owner_user(request)
    # Only shop owners and staff can view kitchen user credentials
    if owner_user.role != 'shop_owner':
        return Response({
            'success': False,
            'message': 'Only shop owners can view kitchen user credentials'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id, role='kitchen_user', restaurant_id=owner_user.id)
        return Response({
            'success': True,
            'data': {
                'username': user.username,
                'password': user.unhashed_password if hasattr(user, 'unhashed_password') else 'Password not available'
            }
        })
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kitchen user not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_kitchen_user_password(request, user_id):
    owner_user = get_owner_user(request)
    # Only shop owners and staff can update kitchen user passwords
    if owner_user.role != 'shop_owner':
        return Response({
            'success': False,
            'message': 'Only shop owners can update kitchen user passwords'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id, role='kitchen_user', restaurant_id=owner_user.id)
        new_password = request.data.get('password')
        
        if not new_password:
            return Response({
                'success': False,
                'message': 'Password is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        if hasattr(user, 'unhashed_password'):
            user.unhashed_password = new_password
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password updated successfully'
        })
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Kitchen user not found'
        }, status=status.HTTP_404_NOT_FOUND)