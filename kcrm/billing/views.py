from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import json

from .models import Customer, Sale, SaleItem, Invoice, InvoiceItem, ProfitPercentage
from .serializers import (
    CustomerSerializer, SaleSerializer, InvoiceSerializer, 
    POSCreateSerializer, StockSerializer
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
                    
                    # Calculate totals from frontend or recalculate
                    if 'total' in data and data['total']:
                        total = Decimal(str(data['total']))
                        subtotal = total + Decimal(str(data.get('discount', 0)))
                    else:
                        # Recalculate if not provided
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
                    
                    # Validate and update stock
                    items_data = []
                    for item in data['items']:
                        try:
                            stock = Stock.objects.get(
                                id=item['id'], 
                                user=request.user, 
                                economic_year=active_eco_year
                            )
                        except Stock.DoesNotExist:
                            return Response({
                                'success': False,
                                'message': f'Stock item not found'
                            }, status=status.HTTP_400_BAD_REQUEST)
                            
                        quantity = Decimal(str(item['quantity']))
                        
                        if stock.current_stock < quantity:
                            return Response({
                                'success': False,
                                'message': f'Insufficient stock for {stock.product_name}'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Get selling price
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
                        
                        total_price = quantity * unit_price
                        
                        items_data.append({
                            'stock': stock,
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'total_price': total_price,
                            'product_name': stock.product_name,
                            'unit': stock.unit
                        })
                    
                    change_amount = data['amount_paid'] - total
                    
                    # Create sale
                    points_earned = data.get('points_earned', 0)
                    sale = Sale.objects.create(
                        sale_number=f"POS-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                        customer_name=data.get('customer_name', ''),
                        customer_phone=data.get('customer_phone', ''),
                        subtotal=subtotal,
                        discount=Decimal(str(data.get('discount', 0))),
                        tax=Decimal('0'),
                        total=total,
                        payment_method=data['payment_method'],
                        amount_paid=data['amount_paid'],
                        change_amount=change_amount,
                        points_earned=points_earned,
                        mode=data.get('mode', 'regular'),
                        cashier=request.user,
                        economic_year=active_eco_year
                    )
                    
                    # Create sale items and update stock
                    for item_data in items_data:
                        SaleItem.objects.create(
                            sale=sale,
                            **item_data
                        )
                        
                        # Update stock quantity
                        stock_item = item_data['stock']
                        stock_item.current_stock -= int(item_data['quantity'])
                        stock_item.save()
                    
                    # Update customer points
                    if data.get('customer_phone'):
                        customer, created = Customer.objects.get_or_create(
                            phone=data['customer_phone'],
                            user=request.user,
                            economic_year=active_eco_year,
                            defaults={
                                'name': data.get('customer_name', ''),
                                'total_purchases': 0,
                                'total_spent': Decimal('0'),
                                'loyalty_points': 0
                            }
                        )
                        if not created and data.get('customer_name'):
                            customer.name = data.get('customer_name')
                        
                        customer.total_purchases += 1
                        customer.total_spent += total
                        customer.loyalty_points += points_earned
                        customer.save()
                        
                        sale.customer = customer
                        sale.save()
                    
                    return Response({
                        'success': True,
                        'sale_id': sale.id,
                        'sale_number': sale.sale_number,
                        'total': float(total),
                        'change': float(change_amount),
                        'points_earned': points_earned
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
            mode_filter = request.query_params.get('mode', None)
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
        today = timezone.now().date()
        
        # Today's stats
        today_sales = Sale.objects.filter(created_at__date=today)
        today_total = sum(sale.total for sale in today_sales)
        today_orders = today_sales.count()
        
        # This week's stats
        week_start = today - timedelta(days=today.weekday())
        week_sales = Sale.objects.filter(created_at__date__gte=week_start)
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

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
            queryset = Invoice.objects.filter(created_by=self.request.user, economic_year=active_eco_year)
        except EconomicYear.DoesNotExist:
            queryset = Invoice.objects.none()
            
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(
                models.Q(invoice_number__icontains=search) |
                models.Q(customer__name__icontains=search)
            )
            
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        from authentication.models import EconomicYear
        active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
        serializer.save(created_by=self.request.user, economic_year=active_eco_year)



class StockViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockSerializer
    
    def get_queryset(self):
        return Stock.objects.none()  # Not used since we override list method

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

class ProfitPercentageViewSet(viewsets.ViewSet):
    def list(self, request):
        try:
            profit = ProfitPercentage.objects.first()
            if profit:
                return Response({
                    'success': True,
                    'data': {'percentage': float(profit.percentage)}
                })
            else:
                return Response({
                    'success': False,
                    'message': 'No profit percentage set'
                })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def create(self, request):
        try:
            percentage = request.data.get('percentage')
            if percentage is None:
                return Response({
                    'success': False,
                    'message': 'Percentage is required'
                }, status=400)
            
            # Delete all existing records and create new one to ensure single record
            ProfitPercentage.objects.all().delete()
            profit = ProfitPercentage.objects.create(
                percentage=percentage,
                updated_by=request.user
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
            if profit_percentage is None:
                return Response({
                    'success': False,
                    'message': 'Profit percentage is required'
                }, status=400)
            
            active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
            purchases = Purchase.objects.filter(user=request.user, economic_year=active_eco_year)
            
            updated_count = 0
            for purchase in purchases:
                new_selling_price = float(purchase.unit_price) * (1 + float(profit_percentage) / 100)
                purchase.selling_price = new_selling_price
                purchase.save()
                updated_count += 1
            
            return Response({
                'success': True,
                'message': f'Updated {updated_count} products',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)