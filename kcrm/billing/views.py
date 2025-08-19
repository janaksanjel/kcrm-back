from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import json

from .models import Customer, Sale, SaleItem, ProfitPercentage, MenuCategory, MenuItem, MenuIngredient, KitchenOrder, KitchenOrderItem
from .serializers import (
    CustomerSerializer, SaleSerializer, 
    POSCreateSerializer, MenuCategorySerializer, MenuItemSerializer, MenuIngredientSerializer,
    KitchenOrderSerializer, StockSerializer
)
from inventory.models import Stock, Category, Supplier, Purchase

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
            queryset = Customer.objects.filter(user=self.request.user, economic_year=active_eco_year)
        except EconomicYear.DoesNotExist:
            queryset = Customer.objects.none()
            
        search = self.request.query_params.get('search', None)
        status_filter = self.request.query_params.get('status', None)
        
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) | 
                models.Q(phone__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        from authentication.models import EconomicYear
        active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
        serializer.save(user=self.request.user, economic_year=active_eco_year)

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

    def get_queryset(self):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
            queryset = Sale.objects.filter(cashier=self.request.user, economic_year=active_eco_year)
        except EconomicYear.DoesNotExist:
            queryset = Sale.objects.none()
            
        date_filter = self.request.query_params.get('date', None)
        payment_method = self.request.query_params.get('payment_method', None)
        mode_filter = self.request.query_params.get('mode', None)
        
        if date_filter:
            queryset = queryset.filter(created_at__date=date_filter)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        if mode_filter:
            queryset = queryset.filter(mode=mode_filter)
            
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def create_pos_sale(self, request):
        serializer = POSCreateSerializer(data=request.data)
        chair_ids = request.data.get('chair_ids', [])
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    data = serializer.validated_data
                    
                    # Get active economic year
                    from authentication.models import EconomicYear
                    try:
                        active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
                    except EconomicYear.DoesNotExist:
                        return Response({
                            'success': False,
                            'message': 'No active economic year found'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Calculate totals
                    if 'total' in data and data['total']:
                        total = Decimal(str(data['total']))
                        subtotal = total + Decimal(str(data.get('discount', 0)))
                    else:
                        subtotal = Decimal('0')
                        for item in data['items']:
                            try:
                                stock = Stock.objects.get(
                                    id=item['id'],
                                    user=request.user,
                                    economic_year=active_eco_year
                                )
                                purchase = Purchase.objects.filter(
                                    product_name=stock.product_name,
                                    user=request.user,
                                    economic_year=active_eco_year
                                ).order_by('-created_at').first()
                                
                                if purchase and purchase.selling_price:
                                    unit_price = Decimal(str(purchase.selling_price))
                                elif purchase:
                                    unit_price = Decimal(str(purchase.unit_price)) * Decimal('1.2')
                                else:
                                    unit_price = Decimal('50')
                                
                                subtotal += unit_price * Decimal(str(item['quantity']))
                            except Stock.DoesNotExist:
                                continue
                        
                        discount = Decimal(str(data.get('discount', 0)))
                        total = subtotal - discount
                    
                    # Handle different modes
                    if data.get('mode') == 'restaurant':
                        # Restaurant mode - create kitchen order
                        try:
                            from .models import Table
                        except ImportError:
                            # Table model might not exist, use default table name
                            Table = None
                        table_id = data.get('table_id', '')
                        table_name = data.get('table_name', '')
                        
                        if table_id and Table:
                            try:
                                table = Table.objects.get(id=table_id, user=request.user)
                                floor_name = table.room.floor.name if table.room and table.room.floor else 'Floor'
                                room_name = table.room.name if table.room else 'Room'
                                table_name = f'{floor_name} - {room_name} - {table.name}'
                            except (Table.DoesNotExist, AttributeError):
                                table_name = f'Table {table_id}'
                        elif table_id:
                            table_name = f'Table {table_id}'
                        elif not table_name.strip() or 'Unknown' in table_name:
                            table_name = f'Order #{timezone.now().strftime("%Y%m%d%H%M%S")}'
                        
                        kitchen_order = KitchenOrder.objects.create(
                            table_id=table_id,
                            table_name=table_name,
                            customer_name=data.get('customer_name', 'Walk-in Customer'),
                            customer_phone=data.get('customer_phone', '0000000000'),
                            chair_ids=chair_ids,
                            total=total,
                            status='pending',
                            user=request.user,
                            economic_year=active_eco_year
                        )
                        
                        # Create KitchenOrderItem objects
                        for item in data['items']:
                            KitchenOrderItem.objects.create(
                                order=kitchen_order,
                                name=item.get('product_name', item.get('name', 'Unknown Item')),
                                quantity=int(item['quantity']),
                                price=float(item.get('unit_price', item.get('price', 0))),
                                total=float(item.get('total_price', item.get('total', 0)))
                            )
                        
                        return Response({
                            'success': True,
                            'message': 'Kitchen order created successfully',
                            'total': float(total)
                        })
                    
                    else:
                        # Kirana/Dealership mode - create sale record
                        # Get or create customer
                        customer = None
                        if data.get('customer_phone') and data.get('customer_phone') != '0000000000':
                            customer, created = Customer.objects.get_or_create(
                                phone=data.get('customer_phone'),
                                user=request.user,
                                economic_year=active_eco_year,
                                defaults={
                                    'name': data.get('customer_name', 'Walk-in Customer'),
                                    'status': 'active'
                                }
                            )
                            if not created and data.get('customer_name'):
                                customer.name = data.get('customer_name')
                                customer.save()
                        
                        # Generate unique sale number
                        import time
                        sale_number = f"{data.get('mode', 'kirana').upper()}-{timezone.now().strftime('%Y%m%d')}-{int(time.time() * 1000) % 1000000}"
                        
                        # Create sale record
                        sale = Sale.objects.create(
                            sale_number=sale_number,
                            customer=customer,
                            customer_name=data.get('customer_name', 'Walk-in Customer'),
                            customer_phone=data.get('customer_phone', '0000000000'),
                            subtotal=subtotal,
                            discount=Decimal(str(data.get('discount', 0))),
                            total=total,
                            payment_method=data.get('payment_method', 'cash'),
                            amount_paid=Decimal(str(data.get('amount_paid', total))),
                            points_earned=data.get('points_earned', 0),
                            mode=data.get('mode', 'kirana'),
                            cashier=request.user,
                            economic_year=active_eco_year
                        )
                        
                        # Create sale items and update stock
                        for item in data['items']:
                            try:
                                stock = Stock.objects.get(
                                    id=item['id'],
                                    user=request.user,
                                    economic_year=active_eco_year
                                )
                                
                                # Create sale item
                                SaleItem.objects.create(
                                    sale=sale,
                                    product_name=item.get('product_name', stock.product_name),
                                    quantity=Decimal(str(item['quantity'])),
                                    unit_price=Decimal(str(item.get('unit_price', 0))),
                                    total_price=Decimal(str(item.get('total_price', 0)))
                                )
                                
                                # Update stock
                                stock.current_stock -= Decimal(str(item['quantity']))
                                stock.save()
                                
                            except Stock.DoesNotExist:
                                continue
                        
                        # Update customer points if customer exists
                        if customer and data.get('points_earned', 0) > 0:
                            customer.loyalty_points = (customer.loyalty_points or 0) + data.get('points_earned', 0)
                            customer.total_spent = (customer.total_spent or 0) + float(total)
                            customer.total_purchases = (customer.total_purchases or 0) + 1
                            customer.save()
                        
                        return Response({
                            'success': True,
                            'message': 'Sale completed successfully',
                            'sale_id': sale.id,
                            'total': float(total)
                        })
                    
            except Exception as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
            today = timezone.now().date()
            
            # Filter by mode if provided
            mode_filter = request.query_params.get('mode', 'kirana')
            today_sales = Sale.objects.filter(
                cashier=request.user, 
                economic_year=active_eco_year,
                created_at__date=today
            )
            
            if mode_filter:
                today_sales = today_sales.filter(mode=mode_filter)
            
            today_total = sum(sale.total for sale in today_sales)
            today_orders = today_sales.count()
            avg_order = float(today_total / today_orders) if today_orders > 0 else 0
            
            return Response({
                'success': True,
                'data': {
                    'todaySales': float(today_total),
                    'todayOrders': today_orders,
                    'avgOrderValue': avg_order,
                    'activeOrders': 0
                }
            })
        except EconomicYear.DoesNotExist:
            return Response({
                'success': True,
                'data': {
                    'todaySales': 0,
                    'todayOrders': 0,
                    'avgOrderValue': 0,
                    'activeOrders': 0
                }
            })

    @action(detail=False, methods=['get'])
    def reports(self, request):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
            today = timezone.now().date()
            mode_filter = request.query_params.get('mode', 'kirana')
            
            # Today's stats
            today_sales = Sale.objects.filter(
                cashier=request.user,
                economic_year=active_eco_year,
                created_at__date=today
            )
            if mode_filter:
                today_sales = today_sales.filter(mode=mode_filter)
                
            today_total = sum(sale.total for sale in today_sales)
            today_orders = today_sales.count()
            
            # This week's stats
            week_start = today - timedelta(days=today.weekday())
            week_sales = Sale.objects.filter(
                cashier=request.user,
                economic_year=active_eco_year,
                created_at__date__gte=week_start
            )
            if mode_filter:
                week_sales = week_sales.filter(mode=mode_filter)
                
            week_total = sum(sale.total for sale in week_sales)
            
            # Payment method breakdown
            payment_stats = {}
            for method in ['cash', 'card', 'upi']:
                payment_stats[method] = sum(
                    sale.total for sale in today_sales.filter(payment_method=method)
                )
            
            # Hourly data for today
            hourly_data = []
            for hour in range(9, 18):  # 9 AM to 5 PM
                hour_sales = today_sales.filter(
                    created_at__hour=hour
                )
                hourly_data.append({
                    'hour': f"{hour}:00",
                    'sales': sum(sale.total for sale in hour_sales),
                    'orders': hour_sales.count()
                })
            
            return Response({
                'success': True,
                'data': {
                    'today': {
                        'total_sales': float(today_total),
                        'total_orders': today_orders,
                        'avg_order_value': float(today_total / today_orders) if today_orders > 0 else 0,
                        'payment_methods': {k: float(v) for k, v in payment_stats.items()},
                        'hourly_data': hourly_data
                    },
                    'week': {
                        'total_sales': float(week_total),
                        'total_orders': week_sales.count()
                    }
                }
            })
        except EconomicYear.DoesNotExist:
            return Response({
                'success': True,
                'data': {
                    'today': {
                        'total_sales': 0,
                        'total_orders': 0,
                        'avg_order_value': 0,
                        'payment_methods': {'cash': 0, 'card': 0, 'upi': 0},
                        'hourly_data': []
                    },
                    'week': {
                        'total_sales': 0,
                        'total_orders': 0
                    }
                }
            })

class StockViewSet(viewsets.ModelViewSet):
    serializer_class = StockSerializer
    
    def get_queryset(self):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
            return Stock.objects.filter(user=self.request.user, economic_year=active_eco_year)
        except EconomicYear.DoesNotExist:
            return Stock.objects.none()

    def list(self, request, *args, **kwargs):
        try:
            from inventory.models import Purchase
            from authentication.models import EconomicYear
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return Response([])
            
            # Get active economic year
            try:
                active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
            except EconomicYear.DoesNotExist:
                # Return empty array if no active economic year
                return Response([])
            
            # Get all stocks for the user and economic year
            stocks = Stock.objects.filter(user=request.user, economic_year=active_eco_year)
            
            # Apply search filter if provided
            search = request.query_params.get('search', None)
            if search:
                stocks = stocks.filter(product_name__icontains=search)
            
            data = []
            for stock in stocks:
                try:
                    # Get purchase info for category and supplier
                    purchase = Purchase.objects.filter(
                        product_name=stock.product_name,
                        user=request.user,
                        economic_year=active_eco_year
                    ).order_by('-created_at').first()
                    
                    category_name = 'General'
                    supplier_name = 'Unknown'
                    cost_price = 0
                    selling_price = 50
                    
                    if purchase:
                        category_name = purchase.category.name if purchase.category else 'General'
                        supplier_name = purchase.supplier.name if purchase.supplier else 'Unknown'
                        cost_price = float(purchase.unit_price)
                        selling_price = float(purchase.selling_price) if purchase.selling_price else float(purchase.unit_price) * 1.2
                    else:
                        # Try to get from any purchase with same product name
                        any_purchase = Purchase.objects.filter(
                            product_name=stock.product_name
                        ).order_by('-created_at').first()
                        if any_purchase:
                            category_name = any_purchase.category.name if any_purchase.category else 'General'
                            supplier_name = any_purchase.supplier.name if any_purchase.supplier else 'Unknown'
                            cost_price = float(any_purchase.unit_price)
                            selling_price = float(any_purchase.selling_price) if any_purchase.selling_price else float(any_purchase.unit_price) * 1.2
                    
                    data.append({
                        'id': stock.id,
                        'name': stock.product_name,
                        'product_name': stock.product_name,
                        'price': selling_price,  # For POS compatibility
                        'stock': stock.current_stock,  # For POS compatibility
                        'quantity': stock.current_stock,
                        'current_stock': stock.current_stock,
                        'unit': stock.unit,
                        'cost_price': cost_price,
                        'selling_price': selling_price,
                        'min_quantity': stock.min_stock,
                        'min_stock': stock.min_stock,
                        'max_quantity': stock.max_stock,
                        'max_stock': stock.max_stock,
                        'category': category_name,  # For POS compatibility
                        'category_name': category_name,
                        'supplier_name': supplier_name,
                        'barcode': str(stock.id),  # Use ID as barcode if not available
                        'updated_at': stock.updated_at.isoformat(),
                        'created_at': stock.created_at.isoformat()
                    })
                except Exception as item_error:
                    # Skip problematic items but continue
                    print(f"Error processing stock item {stock.id}: {str(item_error)}")
                    continue
            
            return Response(data)
            
        except Exception as e:
            import traceback
            print(f"Error in StockViewSet.list: {str(e)}")
            print(traceback.format_exc())
            # Return empty array instead of error to prevent frontend crash
            return Response([])

    @action(detail=False, methods=['get'])
    def debug_info(self, request):
        try:
            from authentication.models import EconomicYear
            
            if not request.user.is_authenticated:
                return Response({'error': 'Not authenticated'})
            
            try:
                active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
            except EconomicYear.DoesNotExist:
                return Response({'error': 'No active economic year'})
            
            stocks_count = Stock.objects.filter(user=request.user, economic_year=active_eco_year).count()
            
            return Response({
                'user': request.user.username,
                'economic_year': active_eco_year.name,
                'stocks_count': stocks_count,
                'message': 'Debug info'
            })
        except Exception as e:
            return Response({'error': str(e)})
    
    @action(detail=False, methods=['get'])
    def inventory_status(self, request):
        try:
            from authentication.models import EconomicYear
            from inventory.models import Purchase
            
            try:
                active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
                stocks = Stock.objects.filter(user=request.user, economic_year=active_eco_year)
            except EconomicYear.DoesNotExist:
                stocks = Stock.objects.none()
            
            total_items = stocks.count()
            in_stock_items = []
            low_stock_items = []
            out_of_stock_items = []
            
            total_value = 0
            
            for stock in stocks:
                try:
                    # Calculate value from purchases
                    purchase = Purchase.objects.filter(
                        product_name=stock.product_name,
                        user=request.user,
                        economic_year=active_eco_year
                    ).order_by('-created_at').first()
                    
                    if purchase:
                        total_value += float(purchase.unit_price) * stock.current_stock
                    
                    if stock.current_stock == 0:
                        out_of_stock_items.append(stock)
                    elif stock.current_stock <= stock.min_stock:
                        low_stock_items.append(stock)
                    else:
                        in_stock_items.append(stock)
                except Exception:
                    # Skip problematic items
                    continue
            
            return Response({
                'success': True,
                'data': {
                    'total_items': total_items,
                    'in_stock': len(in_stock_items),
                    'low_stock': len(low_stock_items),
                    'out_of_stock': len(out_of_stock_items),
                    'expired': 0,  # Not tracked in current Stock model
                    'total_value': total_value,
                    'low_stock_items': [
                        {
                            'id': stock.id,
                            'name': stock.product_name,
                            'current_stock': float(stock.current_stock),
                            'min_stock': float(stock.min_stock),
                            'unit': stock.unit
                        }
                        for stock in low_stock_items
                    ],
                    'out_of_stock_items': [
                        {
                            'id': stock.id,
                            'name': stock.product_name,
                            'unit': stock.unit
                        }
                        for stock in out_of_stock_items
                    ]
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch inventory status'
            }, status=500)

class MenuCategoryViewSet(viewsets.ModelViewSet):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer
    
    def get_queryset(self):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
            queryset = MenuCategory.objects.filter(user=self.request.user, economic_year=active_eco_year)
        except EconomicYear.DoesNotExist:
            queryset = MenuCategory.objects.none()
        
        mode = self.request.query_params.get('mode')
        if mode:
            queryset = queryset.filter(mode=mode)
        
        return queryset.order_by('name')
    
    def perform_create(self, serializer):
        from authentication.models import EconomicYear
        active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
        serializer.save(user=self.request.user, economic_year=active_eco_year)

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
            queryset = MenuItem.objects.filter(user=self.request.user, economic_year=active_eco_year)
        except EconomicYear.DoesNotExist:
            queryset = MenuItem.objects.none()
        
        mode = self.request.query_params.get('mode')
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if mode:
            queryset = queryset.filter(mode=mode)
        if category:
            queryset = queryset.filter(category_id=category)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def perform_create(self, serializer):
        from authentication.models import EconomicYear
        active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
        serializer.save(user=self.request.user, economic_year=active_eco_year)
    
    @action(detail=True, methods=['get', 'post'])
    def ingredients(self, request, pk=None):
        menu_item = self.get_object()
        
        if request.method == 'GET':
            ingredients = MenuIngredient.objects.filter(menu_item=menu_item)
            serializer = MenuIngredientSerializer(ingredients, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            from inventory.models import Stock
            try:
                ingredient_id = request.data.get('ingredient_id')
                quantity = request.data.get('quantity', 1)
                
                # Validate ingredient_id
                if not ingredient_id or ingredient_id == 'undefined' or ingredient_id == 'null':
                    return Response({'error': 'Invalid ingredient ID'}, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    int(ingredient_id)
                except (ValueError, TypeError):
                    return Response({'error': 'Invalid ingredient ID format'}, status=status.HTTP_400_BAD_REQUEST)
                
                ingredient = Stock.objects.get(id=ingredient_id, user=request.user)
                menu_ingredient, created = MenuIngredient.objects.get_or_create(
                    menu_item=menu_item,
                    ingredient=ingredient,
                    defaults={'quantity': quantity}
                )
                
                if not created:
                    menu_ingredient.quantity = quantity
                    menu_ingredient.save()
                
                serializer = MenuIngredientSerializer(menu_ingredient)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Stock.DoesNotExist:
                return Response({'error': 'Ingredient not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch', 'delete'], url_path='ingredients/(?P<ingredient_id>[^/.]+)')
    def ingredient_detail(self, request, pk=None, ingredient_id=None):
        menu_item = self.get_object()
        
        # Validate ingredient_id
        if not ingredient_id or ingredient_id == 'undefined' or ingredient_id == 'null':
            return Response({'error': 'Invalid ingredient ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Convert to int to ensure it's a valid ID
            int(ingredient_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid ingredient ID format'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            menu_ingredient = MenuIngredient.objects.get(
                menu_item=menu_item,
                ingredient_id=ingredient_id
            )
        except MenuIngredient.DoesNotExist:
            return Response({'error': 'Ingredient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'PATCH':
            quantity = request.data.get('quantity')
            if quantity is not None:
                menu_ingredient.quantity = quantity
                menu_ingredient.save()
            serializer = MenuIngredientSerializer(menu_ingredient)
            return Response(serializer.data)
        
        elif request.method == 'DELETE':
            menu_ingredient.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'], url_path='update-stock')
    def update_stock(self, request, pk=None):
        menu_item = self.get_object()
        stock = request.data.get('stock')
        
        if stock is not None and stock >= 0:
            menu_item.stock = stock
            menu_item.save()
            serializer = self.get_serializer(menu_item)
            return Response(serializer.data)
        
        return Response({'error': 'Invalid stock value'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], url_path='toggle-availability')
    def toggle_availability(self, request, pk=None):
        menu_item = self.get_object()
        available = request.data.get('available')
        
        if available is not None:
            menu_item.available = available
            menu_item.save()
            serializer = self.get_serializer(menu_item)
            return Response(serializer.data)
        
        return Response({'error': 'Invalid availability value'}, status=status.HTTP_400_BAD_REQUEST)

class ProfitPercentageViewSet(viewsets.ViewSet):
    def list(self, request):
        try:
            from authentication.models import EconomicYear
            
            eco_year_id = request.query_params.get('eco_year_id')
            mode = request.query_params.get('mode', 'kirana')
            
            # Get economic year
            if eco_year_id:
                try:
                    economic_year = EconomicYear.objects.get(id=eco_year_id, user=request.user)
                except EconomicYear.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Economic year not found'
                    }, status=404)
            else:
                try:
                    economic_year = EconomicYear.objects.get(user=request.user, is_active=True)
                except EconomicYear.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'No active economic year found'
                    }, status=404)
            
            # Get profit percentage for specific eco year and mode
            profit = ProfitPercentage.objects.filter(
                economic_year=economic_year,
                mode=mode
            ).first()
            
            if profit:
                return Response({
                    'success': True,
                    'data': {'percentage': float(profit.percentage)}
                })
            else:
                return Response({
                    'success': False,
                    'message': f'No profit percentage set for {mode} mode in {economic_year.name}'
                })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def create(self, request):
        try:
            from authentication.models import EconomicYear
            
            percentage = request.data.get('percentage')
            eco_year_id = request.data.get('eco_year_id')
            mode = request.data.get('mode', 'kirana')
            
            if percentage is None:
                return Response({
                    'success': False,
                    'message': 'Percentage is required'
                }, status=400)
            
            # Get economic year
            if eco_year_id:
                try:
                    economic_year = EconomicYear.objects.get(id=eco_year_id, user=request.user)
                except EconomicYear.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Economic year not found'
                    }, status=404)
            else:
                try:
                    economic_year = EconomicYear.objects.get(user=request.user, is_active=True)
                except EconomicYear.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'No active economic year found'
                    }, status=404)
            
            # Update or create profit percentage for specific eco year and mode
            profit, created = ProfitPercentage.objects.update_or_create(
                economic_year=economic_year,
                mode=mode,
                defaults={
                    'percentage': percentage,
                    'updated_by': request.user
                }
            )
            
            return Response({
                'success': True,
                'data': {'percentage': float(profit.percentage)}
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def update_selling_prices(self, request):
        try:
            from inventory.models import Purchase
            from authentication.models import EconomicYear
            
            profit_percentage = request.data.get('profit_percentage')
            eco_year_id = request.data.get('eco_year_id')
            mode = request.data.get('mode', 'kirana')
            
            if profit_percentage is None:
                return Response({
                    'success': False,
                    'message': 'Profit percentage is required'
                }, status=400)
            
            # Get economic year
            if eco_year_id:
                try:
                    economic_year = EconomicYear.objects.get(id=eco_year_id, user=request.user)
                except EconomicYear.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Economic year not found'
                    }, status=404)
            else:
                try:
                    economic_year = EconomicYear.objects.get(user=request.user, is_active=True)
                except EconomicYear.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'No active economic year found'
                    }, status=404)
            
            # Filter purchases by mode if needed (assuming purchases have mode field)
            purchases = Purchase.objects.filter(user=request.user, economic_year=economic_year)
            if hasattr(Purchase, 'mode'):
                purchases = purchases.filter(mode=mode)
            
            updated_count = 0
            for purchase in purchases:
                new_selling_price = float(purchase.unit_price) * (1 + float(profit_percentage) / 100)
                purchase.selling_price = new_selling_price
                purchase.save()
                updated_count += 1
            
            return Response({
                'success': True,
                'message': f'Updated {updated_count} products for {mode} mode in {economic_year.name}',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)