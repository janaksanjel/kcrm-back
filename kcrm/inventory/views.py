from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
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
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        categories = Category.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        
        paginator = Paginator(categories, page_size)
        page_obj = paginator.get_page(page)
        serializer = CategorySerializer(page_obj, many=True)
        
        # Calculate stats from all categories
        total_purchases = sum(cat.purchases.count() for cat in categories)
        active_categories = categories.filter(is_active=True).count()
        
        return Response({
            'success': True,
            'categories': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'stats': {
                'total_purchases': total_purchases,
                'active_categories': active_categories,
                'total_categories': paginator.count
            }
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
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        suppliers = Supplier.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        
        paginator = Paginator(suppliers, page_size)
        page_obj = paginator.get_page(page)
        serializer = SupplierSerializer(page_obj, many=True)
        
        return Response({
            'success': True,
            'suppliers': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
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
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        purchases = Purchase.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        
        paginator = Paginator(purchases, page_size)
        page_obj = paginator.get_page(page)
        from .serializers import PurchaseSerializer
        serializer = PurchaseSerializer(page_obj, many=True)
        
        return Response({
            'success': True,
            'purchases': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
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
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        stocks = Stock.objects.filter(user=owner_user, economic_year=active_year, mode=mode)
        
        paginator = Paginator(stocks, page_size)
        page_obj = paginator.get_page(page)
        
        # Enhance stock data with category and supplier information
        enhanced_stocks = []
        for stock in page_obj:
            stock_data = StockSerializer(stock).data
            
            # Get category and supplier names from the stock's foreign keys first
            stock_data['category_name'] = stock.category.name if stock.category else 'General'
            stock_data['supplier_name'] = stock.supplier.name if stock.supplier else 'Unknown'
            
            # If no category/supplier in stock, try to get from latest purchase
            if not stock.category or not stock.supplier:
                try:
                    latest_purchase = Purchase.objects.filter(
                        product_name=stock.product_name,
                        user=owner_user,
                        economic_year=active_year,
                        mode=mode
                    ).order_by('-created_at').first()
                    
                    if latest_purchase:
                        if not stock.category and latest_purchase.category:
                            stock_data['category_name'] = latest_purchase.category.name
                        if not stock.supplier and latest_purchase.supplier:
                            stock_data['supplier_name'] = latest_purchase.supplier.name
                except Exception:
                    pass
            
            enhanced_stocks.append(stock_data)
        
        return Response({
            'success': True,
            'stocks': enhanced_stocks,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
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
            stock.category = purchase.category
            stock.supplier = purchase.supplier
            stock.save()
        
        # Update stock status
        stock.update_status()
        
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
    
    total_categories = Category.objects.filter(user=owner_user, economic_year=active_year, mode=mode).count()
    total_suppliers = Supplier.objects.filter(user=owner_user, economic_year=active_year, mode=mode).count()
    total_purchases = Purchase.objects.filter(user=owner_user, economic_year=active_year, mode=mode).count()
    low_stock_items = Stock.objects.filter(user=owner_user, economic_year=active_year, mode=mode, status='Low').count()
    
    return Response({
        'success': True,
        'data': {
            'totalCategories': total_categories,
            'totalSuppliers': total_suppliers,
            'totalPurchases': total_purchases,
            'lowStockItems': low_stock_items
        }
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def bulk_delete_stocks(request):
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    stock_ids = request.data.get('ids', [])
    if not stock_ids:
        return Response({
            'success': False,
            'message': 'No stock IDs provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        deleted_count = Stock.objects.filter(
            id__in=stock_ids,
            user=owner_user,
            economic_year=active_year
        ).delete()[0]
        
        return Response({
            'success': True,
            'message': f'{deleted_count} stocks deleted successfully',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error deleting stocks: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_stocks(request):
    owner_user = get_owner_user(request)
    active_year = EconomicYear.objects.filter(user=owner_user, is_active=True).first()
    if not active_year:
        return Response({
            'success': False,
            'message': 'No active economic year found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    stocks_data = request.data.get('stocks', [])
    if not stocks_data:
        return Response({
            'success': False,
            'message': 'No stock data provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    created_stocks = []
    errors = []
    
    for stock_data in stocks_data:
        try:
            mode = stock_data.get('mode', 'kirana')
            
            # Handle category - create if doesn't exist
            category = None
            category_name = stock_data.get('category_name', 'General')
            if category_name and category_name.strip():
                category, created = Category.objects.get_or_create(
                    name=category_name.strip(),
                    user=owner_user,
                    economic_year=active_year,
                    mode=mode,
                    defaults={'description': f'Auto-created category for {category_name}'}
                )
            
            # Handle supplier - create if doesn't exist
            supplier = None
            supplier_name = stock_data.get('supplier_name', 'Unknown')
            if supplier_name and supplier_name.strip():
                supplier, created = Supplier.objects.get_or_create(
                    name=supplier_name.strip(),
                    user=owner_user,
                    economic_year=active_year,
                    mode=mode,
                    defaults={
                        'contact': '',
                        'address': f'Auto-created supplier for {supplier_name}',
                        'status': 'Active'
                    }
                )
            
            # Create or update existing stock
            existing_stock = Stock.objects.filter(
                product_name=stock_data.get('product_name'),
                user=owner_user,
                economic_year=active_year,
                mode=mode
            ).first()
            
            if existing_stock:
                # Update existing stock
                existing_stock.current_stock += int(stock_data.get('current_stock', 0))
                existing_stock.selling_price = float(stock_data.get('selling_price', existing_stock.selling_price))
                existing_stock.cost_price = float(stock_data.get('cost_price', existing_stock.cost_price))
                if category:
                    existing_stock.category = category
                if supplier:
                    existing_stock.supplier = supplier
                existing_stock.update_status()
                created_stocks.append(StockSerializer(existing_stock).data)
            else:
                # Prepare data for new stock creation
                new_stock_data = {
                    'product_name': stock_data.get('product_name'),
                    'current_stock': int(stock_data.get('current_stock', 0)),
                    'selling_price': float(stock_data.get('selling_price', 0)),
                    'cost_price': float(stock_data.get('cost_price', 0)),
                    'unit': stock_data.get('unit', 'kg'),
                    'barcode': stock_data.get('barcode', ''),
                    'mode': mode
                }
                
                # Add foreign key IDs if objects exist
                if category:
                    new_stock_data['category'] = category.id
                if supplier:
                    new_stock_data['supplier'] = supplier.id
                
                serializer = StockSerializer(data=new_stock_data, context={'request': request, 'owner_user': owner_user})
                if serializer.is_valid():
                    stock = serializer.save()
                    created_stocks.append(serializer.data)
                else:
                    errors.append(f'Invalid data for {stock_data.get("product_name", "unknown")}: {serializer.errors}')
        except Exception as e:
            errors.append(f'Error processing stock {stock_data.get("product_name", "unknown")}: {str(e)}')
    
    return Response({
        'success': len(created_stocks) > 0,
        'message': f'{len(created_stocks)} stocks processed successfully',
        'created_count': len(created_stocks),
        'error_count': len(errors),
        'data': {'successCount': len(created_stocks), 'errorCount': len(errors)},
        'errors': errors
    })