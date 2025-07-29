from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from authentication.models import EconomicYear
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

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
            if category.products.exists():
                return Response({
                    'success': False,
                    'message': 'Cannot delete category with existing products'
                }, status=status.HTTP_400_BAD_REQUEST)
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
def products(request):
    active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        products = Product.objects.filter(user=request.user, economic_year=active_year)
        category_id = request.GET.get('category')
        if category_id:
            products = products.filter(category_id=category_id)
        
        serializer = ProductSerializer(products, many=True)
        return Response({
            'success': True,
            'products': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Product created successfully',
                'product': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_product(request, product_id):
    try:
        active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
        product = Product.objects.get(id=product_id, user=request.user, economic_year=active_year)
        
        if request.method == 'PUT':
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Product updated successfully',
                    'product': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            product.delete()
            return Response({
                'success': True,
                'message': 'Product deleted successfully'
            })
            
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Product not found'
        }, status=status.HTTP_404_NOT_FOUND)