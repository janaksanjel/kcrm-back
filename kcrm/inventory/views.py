from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from authentication.models import EconomicYear
from .models import Category, Supplier, Purchase
from .serializers import CategorySerializer, SupplierSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def categories(request):
    # Get active economic year
    active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        categories = Category.objects.filter(user=request.user, economic_year=active_year)
        serializer = CategorySerializer(categories, many=True)
        return Response({
            'success': True,
            'categories': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Category created successfully',
                'category': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_category(request, category_id):
    try:
        active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
        category = Category.objects.get(id=category_id, user=request.user, economic_year=active_year)
        
        if request.method == 'PUT':
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Category updated successfully',
                    'category': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            category.delete()
            return Response({
                'success': True,
                'message': 'Category deleted successfully'
            })
            
    except Category.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def suppliers(request):
    active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        suppliers = Supplier.objects.filter(user=request.user, economic_year=active_year)
        serializer = SupplierSerializer(suppliers, many=True)
        return Response({
            'success': True,
            'suppliers': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = SupplierSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Supplier created successfully',
                'supplier': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_supplier(request, supplier_id):
    try:
        active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
        supplier = Supplier.objects.get(id=supplier_id, user=request.user, economic_year=active_year)
        
        if request.method == 'PUT':
            serializer = SupplierSerializer(supplier, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Supplier updated successfully',
                    'supplier': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            supplier.delete()
            return Response({
                'success': True,
                'message': 'Supplier deleted successfully'
            })
            
    except Supplier.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Supplier not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def purchases(request):
    active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        purchases = Purchase.objects.filter(user=request.user, economic_year=active_year)
        from .serializers import PurchaseSerializer
        serializer = PurchaseSerializer(purchases, many=True)
        return Response({
            'success': True,
            'purchases': serializer.data
        })
    
    elif request.method == 'POST':
        from .serializers import PurchaseSerializer
        serializer = PurchaseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Purchase created successfully',
                'purchase': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_purchase(request, purchase_id):
    try:
        active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
        purchase = Purchase.objects.get(id=purchase_id, user=request.user, economic_year=active_year)
        
        if request.method == 'PUT':
            from .serializers import PurchaseSerializer
            serializer = PurchaseSerializer(purchase, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Purchase updated successfully',
                    'purchase': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            purchase.delete()
            return Response({
                'success': True,
                'message': 'Purchase deleted successfully'
            })
            
    except Purchase.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Purchase not found'
        }, status=status.HTTP_404_NOT_FOUND)