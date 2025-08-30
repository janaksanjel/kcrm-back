from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Floor, Room, Table, Chair
from .serializers import FloorSerializer, RoomSerializer, TableSerializer, ChairSerializer
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

class TableSystemViewSet(viewsets.ViewSet):
    def list(self, request):
        from authentication.models import EconomicYear
        try:
            owner_user = get_owner_user(request)
            active_eco_year = EconomicYear.objects.get(user=owner_user, is_active=True)
            floors = Floor.objects.filter(user=owner_user, economic_year=active_eco_year)
            
            data = []
            for floor in floors:
                rooms_data = []
                for room in floor.rooms.all():
                    tables_data = []
                    for table in room.tables.all():
                        chairs_data = [{
                            'id': str(chair.id),
                            'position': chair.position,
                            'occupied': chair.occupied
                        } for chair in table.chairs.all()]
                        
                        tables_data.append({
                            'id': str(table.id),
                            'name': table.name,
                            'status': table.status,
                            'position': {'x': table.position_x, 'y': table.position_y},
                            'chairs': chairs_data
                        })
                    
                    rooms_data.append({
                        'id': str(room.id),
                        'name': room.name,
                        'expanded': room.expanded,
                        'tables': tables_data
                    })
                
                data.append({
                    'id': str(floor.id),
                    'name': floor.name,
                    'expanded': floor.expanded,
                    'rooms': rooms_data
                })
            
            return Response(data)
        except EconomicYear.DoesNotExist:
            return Response([])
    
    @action(detail=False, methods=['post'])
    def create_floor(self, request):
        from authentication.models import EconomicYear
        try:
            owner_user = get_owner_user(request)
            active_eco_year = EconomicYear.objects.get(user=owner_user, is_active=True)
            name = request.data.get('name')
            
            floor = Floor.objects.create(
                name=name,
                user=owner_user,
                economic_year=active_eco_year
            )
            
            return Response({
                'id': str(floor.id),
                'name': floor.name,
                'expanded': floor.expanded,
                'rooms': []
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['post'])
    def create_room(self, request):
        try:
            owner_user = get_owner_user(request)
            floor_id = request.data.get('floor_id')
            name = request.data.get('name')
            
            floor = Floor.objects.get(id=floor_id, user=owner_user)
            room = Room.objects.create(
                name=name,
                floor=floor,
                user=owner_user,
                economic_year=floor.economic_year
            )
            
            return Response({
                'id': str(room.id),
                'name': room.name,
                'expanded': room.expanded,
                'tables': []
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['post'])
    def create_table(self, request):
        try:
            owner_user = get_owner_user(request)
            room_id = request.data.get('room_id')
            name = request.data.get('name')
            chair_count = int(request.data.get('chair_count', 4))
            
            room = Room.objects.get(id=room_id, user=owner_user)
            table = Table.objects.create(
                name=name,
                room=room,
                user=owner_user,
                economic_year=room.economic_year
            )
            
            # Create chairs
            for i in range(1, chair_count + 1):
                Chair.objects.create(
                    table=table,
                    position=i
                )
            
            chairs_data = [{
                'id': str(chair.id),
                'position': chair.position,
                'occupied': chair.occupied
            } for chair in table.chairs.all()]
            
            return Response({
                'id': str(table.id),
                'name': table.name,
                'status': table.status,
                'position': {'x': table.position_x, 'y': table.position_y},
                'chairs': chairs_data
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def update_floor(self, request):
        try:
            owner_user = get_owner_user(request)
            floor_id = request.data.get('floor_id')
            name = request.data.get('name')
            
            floor = Floor.objects.get(id=floor_id, user=owner_user)
            floor.name = name
            floor.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def update_room(self, request):
        try:
            owner_user = get_owner_user(request)
            room_id = request.data.get('room_id')
            name = request.data.get('name')
            
            room = Room.objects.get(id=room_id, user=owner_user)
            room.name = name
            room.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def update_table(self, request):
        try:
            owner_user = get_owner_user(request)
            table_id = request.data.get('table_id')
            name = request.data.get('name')
            position_x = request.data.get('position_x')
            position_y = request.data.get('position_y')
            status_update = request.data.get('status')
            
            table = Table.objects.get(id=table_id, user=owner_user)
            if name:
                table.name = name
            if position_x is not None:
                table.position_x = position_x
            if position_y is not None:
                table.position_y = position_y
            if status_update:
                table.status = status_update
            table.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['get'])
    def get_table_info(self, request):
        try:
            owner_user = get_owner_user(request)
            table_id = request.query_params.get('table_id')
            if not table_id:
                return Response({'error': 'table_id required'}, status=400)
            
            table = Table.objects.get(id=table_id, user=owner_user)
            floor_name = table.room.floor.name if table.room and table.room.floor else 'Unknown Floor'
            room_name = table.room.name if table.room else 'Unknown Room'
            
            return Response({
                'success': True,
                'table_name': f'{floor_name} - {room_name} - {table.name}',
                'floor_name': floor_name,
                'room_name': room_name,
                'table_only_name': table.name,
                'status': table.status
            })
        except Table.DoesNotExist:
            return Response({'error': 'Table not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['delete'])
    def delete_floor(self, request):
        try:
            owner_user = get_owner_user(request)
            floor_id = request.data.get('floor_id')
            floor = Floor.objects.get(id=floor_id, user=owner_user)
            floor.delete()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['delete'])
    def delete_room(self, request):
        try:
            owner_user = get_owner_user(request)
            room_id = request.data.get('room_id')
            room = Room.objects.get(id=room_id, user=owner_user)
            room.delete()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['delete'])
    def delete_table(self, request):
        try:
            owner_user = get_owner_user(request)
            table_id = request.data.get('table_id')
            table = Table.objects.get(id=table_id, user=owner_user)
            table.delete()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def toggle_chair(self, request):
        try:
            owner_user = get_owner_user(request)
            chair_id = request.data.get('chair_id')
            chair = Chair.objects.get(id=chair_id, table__user=owner_user)
            chair.occupied = not chair.occupied
            chair.save()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def update_chair_count(self, request):
        try:
            owner_user = get_owner_user(request)
            table_id = request.data.get('table_id')
            chair_count = int(request.data.get('chair_count', 4))
            
            table = Table.objects.get(id=table_id, user=owner_user)
            
            # Delete existing chairs
            table.chairs.all().delete()
            
            # Create new chairs
            for i in range(1, chair_count + 1):
                Chair.objects.create(
                    table=table,
                    position=i
                )
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def sync_chair_occupancy(self, request):
        try:
            from .models import KitchenOrder
            owner_user = get_owner_user(request)
            table_id = request.data.get('table_id')
            
            table = Table.objects.get(id=table_id, user=owner_user)
            
            # Check for active orders
            active_order = KitchenOrder.objects.filter(
                table_id=table_id,
                status__in=['pending', 'preparing', 'ready'],
                user=owner_user
            ).first()
            
            if active_order and active_order.chair_ids:
                # Mark specific chairs as occupied
                table.chairs.update(occupied=False)  # Reset all first
                for chair_id in active_order.chair_ids:
                    Chair.objects.filter(id=chair_id).update(occupied=True)
            else:
                # No active order, mark all chairs as available
                table.chairs.update(occupied=False)
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def mark_chairs_occupied(self, request):
        try:
            owner_user = get_owner_user(request)
            chair_ids = request.data.get('chair_ids', [])
            
            for chair_id in chair_ids:
                chair = Chair.objects.get(id=chair_id, table__user=owner_user)
                chair.occupied = True
                chair.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)