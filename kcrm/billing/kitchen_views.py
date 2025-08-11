from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import KitchenOrder, KitchenOrderItem
from .serializers import KitchenOrderSerializer

class KitchenOrderViewSet(viewsets.ModelViewSet):
    queryset = KitchenOrder.objects.all()
    serializer_class = KitchenOrderSerializer
    
    def get_queryset(self):
        from authentication.models import EconomicYear, User
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Kitchen orders request from user: {self.request.user.username}, role: {self.request.user.role}, restaurant_id: {self.request.user.restaurant_id}")
            
            # For kitchen users, get orders from their restaurant owner
            if self.request.user.role == 'kitchen_user' and self.request.user.restaurant_id:
                # Find the restaurant owner with the same restaurant_id
                restaurant_owner = User.objects.filter(
                    id=self.request.user.restaurant_id,
                    role='shop_owner'
                ).first()
                
                logger.info(f"Found restaurant owner: {restaurant_owner}")
                
                if restaurant_owner:
                    active_eco_year = EconomicYear.objects.get(user=restaurant_owner, is_active=True)
                    orders = KitchenOrder.objects.filter(user=restaurant_owner, economic_year=active_eco_year).order_by('-created_at')
                    logger.info(f"Kitchen orders found: {orders.count()}")
                    return orders
            else:
                # For restaurant owners, get their own orders
                active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
                orders = KitchenOrder.objects.filter(user=self.request.user, economic_year=active_eco_year).order_by('-created_at')
                logger.info(f"Restaurant owner orders found: {orders.count()}")
                return orders
        except EconomicYear.DoesNotExist:
            logger.error("No active economic year found")
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
        
        return KitchenOrder.objects.none()
    
    def perform_create(self, serializer):
        from authentication.models import EconomicYear
        active_eco_year = EconomicYear.objects.get(user=self.request.user, is_active=True)
        serializer.save(user=self.request.user, economic_year=active_eco_year)
    
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        order = self.get_object()
        status_value = request.data.get('status')
        
        if status_value in ['pending', 'preparing', 'ready', 'served', 'completed']:
            order.status = status_value
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        order = self.get_object()
        order.status = 'completed'
        order.save()
        return Response({'success': True})