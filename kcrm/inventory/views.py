from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from authentication.models import EconomicYear
from .models import Category, Supplier, Purchase, Stock
from .serializers import CategorySerializer, SupplierSerializer, StockSerializer
from django.db.models import Sum, Count

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

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def stocks(request):
    active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        stocks = Stock.objects.filter(user=request.user, economic_year=active_year)
        serializer = StockSerializer(stocks, many=True)
        return Response({
            'success': True,
            'stocks': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = StockSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Stock created successfully',
                'stock': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_stock(request, stock_id):
    try:
        active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
        stock = Stock.objects.get(id=stock_id, user=request.user, economic_year=active_year)
        
        if request.method == 'PUT':
            serializer = StockSerializer(stock, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Stock updated successfully',
                    'stock': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            stock.delete()
            return Response({
                'success': True,
                'message': 'Stock deleted successfully'
            })
            
    except Stock.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Stock not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports(request):
    active_year = EconomicYear.objects.filter(user=request.user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get all data
    stocks = Stock.objects.filter(user=request.user, economic_year=active_year)
    purchases = Purchase.objects.filter(user=request.user, economic_year=active_year)
    suppliers = Supplier.objects.filter(user=request.user, economic_year=active_year)
    categories = Category.objects.filter(user=request.user, economic_year=active_year)
    
    # Calculate inventory summary
    total_value = sum(stock.current_stock * 50 for stock in stocks)  # Assuming avg price 50
    total_products = stocks.count()
    low_stock_items = stocks.filter(status='Low').count()
    out_of_stock_items = stocks.filter(current_stock=0).count()
    
    # Category performance
    category_performance = []
    for category in categories:
        category_purchases = purchases.filter(category=category)
        category_value = sum(p.total_amount for p in category_purchases)
        category_performance.append({
            'category': category.name,
            'products': category_purchases.count(),
            'value': float(category_value),
            'percentage': round((category_value / max(sum(p.total_amount for p in purchases), 1)) * 100, 1)
        })
    
    # Supplier payments
    supplier_payments = []
    for supplier in suppliers:
        supplier_purchases = purchases.filter(supplier=supplier)
        total_paid = sum(p.total_amount for p in supplier_purchases.filter(payment_status='paid'))
        total_due = sum(p.total_amount for p in supplier_purchases.filter(payment_status='pending'))
        supplier_payments.append({
            'supplier': supplier.name,
            'total_paid': float(total_paid),
            'total_due': float(total_due),
            'orders': supplier_purchases.count()
        })
    
    # Top products by purchase quantity
    from django.db.models import Sum
    top_products = purchases.values('product_name').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum('total_amount')
    ).order_by('-total_quantity')[:5]
    
    return Response({
        'success': True,
        'reports': {
            'inventory_summary': {
                'total_value': float(total_value),
                'total_products': total_products,
                'low_stock_items': low_stock_items,
                'out_of_stock_items': out_of_stock_items
            },
            'category_performance': category_performance,
            'supplier_payments': supplier_payments,
            'top_products': [
                {
                    'name': item['product_name'],
                    'quantity': item['total_quantity'],
                    'value': float(item['total_value'])
                } for item in top_products
            ]
        }
    })