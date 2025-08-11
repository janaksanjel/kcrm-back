from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Floor, Room, Table, Chair
from .serializers import FloorSerializer, RoomSerializer, TableSerializer, ChairSerializer

class TableSystemViewSet(viewsets.ViewSet):
    def list(self, request):
        from authentication.models import EconomicYear
        try:
            active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
            floors = Floor.objects.filter(user=request.user, economic_year=active_eco_year)
            
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
            active_eco_year = EconomicYear.objects.get(user=request.user, is_active=True)
            name = request.data.get('name')
            
            floor = Floor.objects.create(
                name=name,
                user=request.user,
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
            floor_id = request.data.get('floor_id')
            name = request.data.get('name')
            
            floor = Floor.objects.get(id=floor_id, user=request.user)
            room = Room.objects.create(
                name=name,
                floor=floor,
                user=request.user,
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
            room_id = request.data.get('room_id')
            name = request.data.get('name')
            chair_count = int(request.data.get('chair_count', 4))
            
            room = Room.objects.get(id=room_id, user=request.user)
            table = Table.objects.create(
                name=name,
                room=room,
                user=request.user,
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
            floor_id = request.data.get('floor_id')
            name = request.data.get('name')
            
            floor = Floor.objects.get(id=floor_id, user=request.user)
            floor.name = name
            floor.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def update_room(self, request):
        try:
            room_id = request.data.get('room_id')
            name = request.data.get('name')
            
            room = Room.objects.get(id=room_id, user=request.user)
            room.name = name
            room.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def update_table(self, request):
        try:
            table_id = request.data.get('table_id')
            name = request.data.get('name')
            position_x = request.data.get('position_x')
            position_y = request.data.get('position_y')
            
            table = Table.objects.get(id=table_id, user=request.user)
            if name:
                table.name = name
            if position_x is not None:
                table.position_x = position_x
            if position_y is not None:
                table.position_y = position_y
            table.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['delete'])
    def delete_floor(self, request):
        try:
            floor_id = request.data.get('floor_id')
            floor = Floor.objects.get(id=floor_id, user=request.user)
            floor.delete()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['delete'])
    def delete_room(self, request):
        try:
            room_id = request.data.get('room_id')
            room = Room.objects.get(id=room_id, user=request.user)
            room.delete()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['delete'])
    def delete_table(self, request):
        try:
            table_id = request.data.get('table_id')
            table = Table.objects.get(id=table_id, user=request.user)
            table.delete()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def toggle_chair(self, request):
        try:
            chair_id = request.data.get('chair_id')
            chair = Chair.objects.get(id=chair_id, table__user=request.user)
            chair.occupied = not chair.occupied
            chair.save()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['patch'])
    def update_chair_count(self, request):
        try:
            table_id = request.data.get('table_id')
            chair_count = int(request.data.get('chair_count', 4))
            
            table = Table.objects.get(id=table_id, user=request.user)
            
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