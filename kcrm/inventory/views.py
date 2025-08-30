from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from authentication.models import EconomicYear
from .models import Category, Supplier, Purchase, Stock
from .serializers import CategorySerializer, SupplierSerializer, StockSerializer
from django.db.models import Sum, Count
from staff.models import Staff

def get_owner_user(request):
    """Get the shop owner user for staff or return the user itself for shop owners"""
    if request.user.role == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            return staff.shop_owner
        except Staff.DoesNotExist:
            return request.user
    return request.user

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def categories(request):
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        mode = request.GET.get('mode', 'kirana')
        try:
            categories = Category.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        except Exception as e:
            categories = Category.objects.filter(user=owner_user, economic_year=active_year)
        serializer = CategorySerializer(categories, many=True)
        return Response({
            'success': True,
            'categories': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data, context={'request': request, 'owner_user': owner_user})
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
        owner_user = get_owner_user(request)
        active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
        category = Category.objects.get(id=category_id, user=owner_user, economic_year=active_year)
        
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
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        mode = request.GET.get('mode', 'kirana')
        try:
            suppliers = Supplier.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        except Exception as e:
            suppliers = Supplier.objects.filter(user=owner_user, economic_year=active_year)
        serializer = SupplierSerializer(suppliers, many=True)
        return Response({
            'success': True,
            'suppliers': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = SupplierSerializer(data=request.data, context={'request': request, 'owner_user': owner_user})
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
        owner_user = get_owner_user(request)
        active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
        supplier = Supplier.objects.get(id=supplier_id, user=owner_user, economic_year=active_year)
        
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
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        mode = request.GET.get('mode', 'kirana')
        try:
            purchases = Purchase.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        except Exception as e:
            purchases = Purchase.objects.filter(user=owner_user, economic_year=active_year)
        from .serializers import PurchaseSerializer
        serializer = PurchaseSerializer(purchases, many=True)
        return Response({
            'success': True,
            'purchases': serializer.data
        })
    
    elif request.method == 'POST':
        from .serializers import PurchaseSerializer
        serializer = PurchaseSerializer(data=request.data, context={'request': request, 'owner_user': owner_user})
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
        owner_user = get_owner_user(request)
        active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
        purchase = Purchase.objects.get(id=purchase_id, user=owner_user, economic_year=active_year)
        
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
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        mode = request.GET.get('mode', 'kirana')
        try:
            stocks = Stock.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        except Exception as e:
            stocks = Stock.objects.filter(user=owner_user, economic_year=active_year)
        
        # Enhance stock data with purchase information
        enhanced_stocks = []
        for stock in stocks:
            stock_data = StockSerializer(stock).data
            
            # Get related purchase data for category, supplier, and prices
            try:
                latest_purchase = Purchase.objects.filter(
                    product_name=stock.product_name,
                    user=owner_user,
                    economic_year=active_year,
                    mode=mode
                ).order_by('-created_at').first()
                
                if latest_purchase:
                    stock_data['category_name'] = latest_purchase.category.name if latest_purchase.category else 'General'
                    stock_data['supplier_name'] = latest_purchase.supplier.name if latest_purchase.supplier else 'Unknown'
                    # Use stock's cost_price if available, otherwise use purchase unit_price
                    stock_data['cost_price'] = float(stock.cost_price) if stock.cost_price > 0 else float(latest_purchase.unit_price)
                    # Use stock's selling_price if available, otherwise use purchase selling_price
                    stock_data['selling_price'] = float(stock.selling_price) if stock.selling_price > 0 else (float(latest_purchase.selling_price) if latest_purchase.selling_price else float(latest_purchase.unit_price) * 1.2)
                else:
                    stock_data['category_name'] = 'General'
                    stock_data['supplier_name'] = 'Unknown'
                    stock_data['cost_price'] = float(stock.cost_price) if stock.cost_price > 0 else 0
                    stock_data['selling_price'] = float(stock.selling_price) if stock.selling_price > 0 else 0
            except Exception as e:
                stock_data['category_name'] = 'General'
                stock_data['supplier_name'] = 'Unknown'
                stock_data['cost_price'] = 0
                stock_data['selling_price'] = 0
            
            enhanced_stocks.append(stock_data)
        
        return Response({
            'success': True,
            'stocks': enhanced_stocks
        })
    
    elif request.method == 'POST':
        serializer = StockSerializer(data=request.data, context={'request': request, 'owner_user': owner_user})
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
        owner_user = get_owner_user(request)
        active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
        stock = Stock.objects.get(id=stock_id, user=owner_user, economic_year=active_year)
        
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
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    mode = request.GET.get('mode', 'kirana')
    
    stocks = Stock.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
    purchases = Purchase.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
    suppliers = Supplier.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
    categories = Category.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
    
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def untransfer_from_stock(request, purchase_id):
    try:
        owner_user = get_owner_user(request)
        active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
        if not active_year:
            return Response({
                'success': False,
                'message': 'No active economic year found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        purchase = Purchase.objects.get(id=purchase_id, user=owner_user, economic_year=active_year)
        
        # Check if not transferred
        if not purchase.isTransferredStock:
            return Response({
                'success': False,
                'message': 'Purchase is not transferred to stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find and update stock
        try:
            stock = Stock.objects.get(
                product_name=purchase.product_name,
                user=owner_user,
                economic_year=active_year,
                mode=purchase.mode
            )
            
            # Reduce stock quantity
            if stock.current_stock >= purchase.quantity:
                stock.current_stock -= purchase.quantity
                if stock.current_stock == 0:
                    stock.delete()
                else:
                    stock.save()
            else:
                return Response({
                    'success': False,
                    'message': 'Insufficient stock to untransfer'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Stock.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Stock not found for this product'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Mark purchase as not transferred
        purchase.isTransferredStock = False
        purchase.save()
        
        return Response({
            'success': True,
            'message': 'Purchase untransferred from stock successfully'
        })
        
    except Purchase.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Purchase not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error untransferring from stock: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_to_stock(request, purchase_id):
    try:
        owner_user = get_owner_user(request)
        active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
        if not active_year:
            return Response({
                'success': False,
                'message': 'No active economic year found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        purchase = Purchase.objects.get(id=purchase_id, user=owner_user, economic_year=active_year)
        
        # Check if already transferred
        if purchase.isTransferredStock:
            return Response({
                'success': False,
                'message': 'Purchase already transferred to stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update stock
        stock, created = Stock.objects.get_or_create(
            product_name=purchase.product_name,
            user=owner_user,
            economic_year=active_year,
            mode=purchase.mode,
            defaults={
                'current_stock': purchase.quantity,
                'unit': purchase.unit,
                'min_stock': 10,
                'max_stock': 100,
                'cost_price': purchase.unit_price,
                'selling_price': purchase.selling_price or purchase.unit_price * 1.2,
                'category': purchase.category,
                'supplier': purchase.supplier
            }
        )
        
        if not created:
            # Update existing stock
            stock.current_stock += purchase.quantity
            stock.cost_price = purchase.unit_price
            stock.selling_price = purchase.selling_price or purchase.unit_price * 1.2
            stock.save()
        
        # Mark purchase as transferred
        purchase.isTransferredStock = True
        purchase.save()
        
        return Response({
            'success': True,
            'message': 'Purchase transferred to stock successfully',
            'stock_id': stock.id
        })
        
    except Purchase.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Purchase not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error transferring to stock: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    mode = request.GET.get('mode', 'kirana')
    
    try:
        total_categories = Category.objects.filter(user=owner_user, economic_year=active_year, mode=mode).count()
        total_suppliers = Supplier.objects.filter(user=owner_user, economic_year=active_year, mode=mode).count()
        total_purchases = Purchase.objects.filter(user=owner_user, economic_year=active_year, mode=mode).count()
        low_stock_items = Stock.objects.filter(user=owner_user, economic_year=active_year, mode=mode, status='Low').count()
    except Exception as e:
        total_categories = Category.objects.filter(user=owner_user, economic_year=active_year).count()
        total_suppliers = Supplier.objects.filter(user=owner_user, economic_year=active_year).count()
        total_purchases = Purchase.objects.filter(user=owner_user, economic_year=active_year).count()
        low_stock_items = Stock.objects.filter(user=owner_user, economic_year=active_year, status='Low').count()
    
    return Response({
        'success': True,
        'data': {
            'totalCategories': total_categories,
            'totalSuppliers': total_suppliers,
            'totalPurchases': total_purchases,
            'lowStockItems': low_stock_items
        }
    })