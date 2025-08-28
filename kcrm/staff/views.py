from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Role, UserRole, Staff
from .serializers import RoleSerializer, UserRoleSerializer, StaffSerializer
from authentication.models import EconomicYear

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def roles(request):
    if request.method == 'GET':
        try:
            active_year = EconomicYear.objects.get(user=request.user, is_active=True)
            mode = request.GET.get('mode', 'kirana')
            
            roles = Role.objects.filter(
                user=request.user,
                economic_year=active_year,
                mode=mode,
                is_active=True
            )
            
            serializer = RoleSerializer(roles, many=True)
            return Response({
                'success': True,
                'roles': serializer.data
            })
        except EconomicYear.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No active economic year found'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'POST':
        serializer = RoleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            role = serializer.save()
            return Response({
                'success': True,
                'message': 'Role created successfully',
                'role': RoleSerializer(role).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_role(request, role_id):
    try:
        active_year = EconomicYear.objects.get(user=request.user, is_active=True)
        role = Role.objects.get(id=role_id, user=request.user, economic_year=active_year)
        
        if request.method == 'GET':
            serializer = RoleSerializer(role)
            return Response({
                'success': True,
                'role': serializer.data
            })
        
        elif request.method == 'PUT':
            serializer = RoleSerializer(role, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                role = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Role updated successfully',
                    'role': RoleSerializer(role).data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            role.is_active = False
            role.save()
            return Response({
                'success': True,
                'message': 'Role deleted successfully'
            })
    
    except EconomicYear.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Role.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Role not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permissions(request):
    mode = request.GET.get('mode', 'kirana')
    
    # Define permission structure for each mode
    permission_structure = {
        'kirana': {
            'dashboard': {'name': 'Dashboard', 'tabs': []},
            'inventory': {
                'name': 'Inventory',
                'tabs': [
                    {'id': 'inventory_stock', 'name': 'Stock'},
                    {'id': 'inventory_categories', 'name': 'Categories'},
                    {'id': 'inventory_suppliers', 'name': 'Suppliers'},
                    {'id': 'inventory_purchases', 'name': 'Purchases'},
                    {'id': 'inventory_reports', 'name': 'Reports'}
                ]
            },
            'billing': {
                'name': 'Billing System',
                'tabs': [
                    {'id': 'billing_inventory', 'name': 'Inventory'},
                    {'id': 'billing_add_product', 'name': 'Add Product'},
                    {'id': 'billing_pos', 'name': 'POS'},
                    {'id': 'billing_receipts', 'name': 'Receipts'},
                    {'id': 'billing_customers', 'name': 'Customers'},
                    {'id': 'billing_reports', 'name': 'Reports'}
                ]
            },
            'reports': {
                'name': 'Reports',
                'tabs': [
                    {'id': 'reports_sales', 'name': 'Sales Report'},
                    {'id': 'reports_inventory', 'name': 'Inventory Report'},
                    {'id': 'reports_financial', 'name': 'Financial Report'},
                    {'id': 'reports_customer', 'name': 'Customer Report'},
                    {'id': 'reports_performance', 'name': 'Performance'}
                ]
            },
            'staff': {
                'name': 'Staff Management',
                'tabs': [
                    {'id': 'staff_roles', 'name': 'Roles'},
                    {'id': 'staff_list', 'name': 'Staff List'},
                    {'id': 'staff_permissions', 'name': 'Permissions'},
                    {'id': 'staff_attendance', 'name': 'Attendance'},
                    {'id': 'staff_reports', 'name': 'Reports'}
                ]
            },
            'settings': {
                'name': 'Settings',
                'tabs': [
                    {'id': 'settings_profile', 'name': 'Profile'},
                    {'id': 'settings_password', 'name': 'Password'},
                    {'id': 'settings_sessions', 'name': 'Sessions'},
                    {'id': 'settings_economic_year', 'name': 'Economic Year'},
                    {'id': 'settings_notifications', 'name': 'Notifications'},
                    {'id': 'settings_security', 'name': 'Security'}
                ]
            }
        },
        'restaurant': {
            'dashboard': {'name': 'Dashboard', 'tabs': []},
            'inventory': {
                'name': 'Inventory',
                'tabs': [
                    {'id': 'inventory_ingredients', 'name': 'Ingredients'},
                    {'id': 'inventory_categories', 'name': 'Categories'},
                    {'id': 'inventory_suppliers', 'name': 'Suppliers'},
                    {'id': 'inventory_purchases', 'name': 'Purchases'},
                    {'id': 'inventory_reports', 'name': 'Reports'}
                ]
            },
            'billing': {
                'name': 'Billing System',
                'tabs': [
                    {'id': 'billing_ingredients', 'name': 'Ingredients'},
                    {'id': 'billing_menu_items', 'name': 'Menu Items'},
                    {'id': 'billing_pos', 'name': 'POS'},
                    {'id': 'billing_billing', 'name': 'Billing'},
                    {'id': 'billing_receipts', 'name': 'Receipts'},
                    {'id': 'billing_customers', 'name': 'Customers'},
                    {'id': 'billing_tables', 'name': 'Tables'},
                    {'id': 'billing_kitchen_orders', 'name': 'Kitchen Orders'},
                    {'id': 'billing_create_kitchen_user', 'name': 'Create Kitchen User'}
                ]
            },
            'reports': {
                'name': 'Reports',
                'tabs': [
                    {'id': 'reports_sales', 'name': 'Sales Report'},
                    {'id': 'reports_inventory', 'name': 'Inventory Report'},
                    {'id': 'reports_financial', 'name': 'Financial Report'},
                    {'id': 'reports_customer', 'name': 'Customer Report'},
                    {'id': 'reports_performance', 'name': 'Performance'}
                ]
            },
            'staff': {
                'name': 'Staff Management',
                'tabs': [
                    {'id': 'staff_roles', 'name': 'Roles'},
                    {'id': 'staff_list', 'name': 'Staff List'},
                    {'id': 'staff_permissions', 'name': 'Permissions'},
                    {'id': 'staff_attendance', 'name': 'Attendance'},
                    {'id': 'staff_reports', 'name': 'Reports'}
                ]
            },
            'settings': {
                'name': 'Settings',
                'tabs': [
                    {'id': 'settings_profile', 'name': 'Profile'},
                    {'id': 'settings_password', 'name': 'Password'},
                    {'id': 'settings_sessions', 'name': 'Sessions'},
                    {'id': 'settings_economic_year', 'name': 'Economic Year'},
                    {'id': 'settings_notifications', 'name': 'Notifications'},
                    {'id': 'settings_security', 'name': 'Security'}
                ]
            }
        },
        'dealership': {
            'dashboard': {'name': 'Dashboard', 'tabs': []},
            'inventory': {
                'name': 'Inventory',
                'tabs': [
                    {'id': 'inventory_categories', 'name': 'Categories'},
                    {'id': 'inventory_suppliers', 'name': 'Suppliers'},
                    {'id': 'inventory_purchases', 'name': 'Purchases'},
                    {'id': 'inventory_stock_management', 'name': 'Stock Management'},
                    {'id': 'inventory_reports', 'name': 'Reports'}
                ]
            },
            'billing': {
                'name': 'Billing System',
                'tabs': [
                    {'id': 'billing_inventory', 'name': 'Inventory'},
                    {'id': 'billing_your_product', 'name': 'Your Product'},
                    {'id': 'billing_pos_system', 'name': 'POS System'},
                    {'id': 'billing_receipts', 'name': 'Receipts'},
                    {'id': 'billing_customers', 'name': 'Customers'},
                    {'id': 'billing_reports', 'name': 'Reports'}
                ]
            },
            'reports': {
                'name': 'Reports',
                'tabs': [
                    {'id': 'reports_sales', 'name': 'Sales Report'},
                    {'id': 'reports_inventory', 'name': 'Inventory Report'},
                    {'id': 'reports_financial', 'name': 'Financial Report'},
                    {'id': 'reports_customer', 'name': 'Customer Report'},
                    {'id': 'reports_performance', 'name': 'Performance'}
                ]
            },
            'staff': {
                'name': 'Staff Management',
                'tabs': [
                    {'id': 'staff_roles', 'name': 'Roles'},
                    {'id': 'staff_list', 'name': 'Staff List'},
                    {'id': 'staff_permissions', 'name': 'Permissions'},
                    {'id': 'staff_attendance', 'name': 'Attendance'},
                    {'id': 'staff_reports', 'name': 'Reports'}
                ]
            },
            'settings': {
                'name': 'Settings',
                'tabs': [
                    {'id': 'settings_profile', 'name': 'Profile'},
                    {'id': 'settings_password', 'name': 'Password'},
                    {'id': 'settings_sessions', 'name': 'Sessions'},
                    {'id': 'settings_economic_year', 'name': 'Economic Year'},
                    {'id': 'settings_notifications', 'name': 'Notifications'},
                    {'id': 'settings_security', 'name': 'Security'}
                ]
            }
        }
    }
    
    return Response({
        'success': True,
        'permissions': permission_structure.get(mode, permission_structure['kirana'])
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_role(request):
    serializer = UserRoleSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user_role = serializer.save()
        return Response({
            'success': True,
            'message': 'Role assigned successfully',
            'user_role': UserRoleSerializer(user_role).data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_roles(request, user_id):
    try:
        active_year = EconomicYear.objects.get(user=request.user, is_active=True)
        user_roles = UserRole.objects.filter(
            user_id=user_id,
            role__user=request.user,
            role__economic_year=active_year,
            is_active=True
        )
        
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response({
            'success': True,
            'user_roles': serializer.data
        })
    except EconomicYear.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)

# Staff Management
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def staff_list(request):
    if request.method == 'GET':
        try:
            active_year = EconomicYear.objects.get(user=request.user, is_active=True)
            mode = request.GET.get('mode', 'kirana')
            
            staff = Staff.objects.filter(
                created_by=request.user,
                economic_year=active_year,
                mode=mode
            ).order_by('-created_at')
            
            staff_data = []
            for s in staff:
                data = StaffSerializer(s).data
                data['password'] = s.auto_password
                staff_data.append(data)
            
            return Response({
                'success': True,
                'staff': staff_data
            })
        except EconomicYear.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No active economic year found'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'POST':
        serializer = StaffSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                staff = serializer.save()
                # Show password in response for first time
                serializer._password_shown = True
                response_data = serializer.to_representation(staff)
                response_data['password'] = staff.auto_password
                
                return Response({
                    'success': True,
                    'message': 'Staff member added successfully',
                    'staff': response_data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e) or 'email' in str(e).lower():
                    return Response({
                        'success': False,
                        'message': 'Email already in use'
                    }, status=status.HTTP_400_BAD_REQUEST)
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def staff_detail(request, staff_id):
    try:
        active_year = EconomicYear.objects.get(user=request.user, is_active=True)
        staff = Staff.objects.get(
            id=staff_id,
            created_by=request.user,
            economic_year=active_year
        )
        
        if request.method == 'GET':
            serializer = StaffSerializer(staff)
            return Response({
                'success': True,
                'staff': serializer.data
            })
        
        elif request.method == 'PUT':
            serializer = StaffSerializer(staff, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Staff member updated successfully',
                    'staff': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Actually delete the staff member
            if staff.user:
                staff.user.delete()
            staff.delete()
            
            return Response({
                'success': True,
                'message': 'Staff member deleted successfully'
            })
    
    except EconomicYear.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Staff.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Staff member not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_staff_password(request, staff_id):
    try:
        active_year = EconomicYear.objects.get(user=request.user, is_active=True)
        staff = Staff.objects.get(
            id=staff_id,
            created_by=request.user,
            economic_year=active_year
        )
        
        new_password = request.data.get('password')
        if not new_password:
            return Response({
                'success': False,
                'message': 'Password is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update staff password
        staff.auto_password = new_password
        staff.save()
        
        # Update user password
        if staff.user:
            staff.user.set_password(new_password)
            staff.user.save()
        
        return Response({
            'success': True,
            'message': 'Password updated successfully'
        })
    
    except EconomicYear.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Staff.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Staff member not found'
        }, status=status.HTTP_404_NOT_FOUND)