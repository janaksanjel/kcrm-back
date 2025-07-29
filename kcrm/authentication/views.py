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
    ProfileUpdateSerializer, PasswordChangeSerializer, UserSessionSerializer, EconomicYearSerializer,
    NotificationSettingsSerializer, SecuritySettingsSerializer, SecurityActivitySerializer
)
from .models import UserSession, EconomicYear, NotificationSettings, SecuritySettings, SecurityActivity

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        
        # Create session record for new user
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
def profile(request):
    user_data = UserSerializer(request.user).data
    return Response({
        'success': True,
        'user': user_data
    }, status=status.HTTP_200_OK)

# Settings APIs
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
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
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
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

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
    if request.method == 'GET':
        years = EconomicYear.objects.filter(user=request.user).order_by('-created_at')
        serializer = EconomicYearSerializer(years, many=True)
        return Response({
            'success': True,
            'economic_years': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = EconomicYearSerializer(data=request.data, context={'request': request})
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

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_economic_year(request, year_id):
    try:
        year = EconomicYear.objects.get(id=year_id, user=request.user)
        if year.is_default:
            return Response({
                'success': False,
                'message': 'Cannot delete default economic year'
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
def set_default_economic_year(request, year_id):
    try:
        # Remove default from all years
        EconomicYear.objects.filter(user=request.user).update(is_default=False)
        # Set new default
        year = EconomicYear.objects.get(id=year_id, user=request.user)
        year.is_default = True
        year.save()
        return Response({
            'success': True,
            'message': 'Default economic year updated successfully'
        })
    except EconomicYear.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Economic year not found'
        }, status=status.HTTP_404_NOT_FOUND)

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