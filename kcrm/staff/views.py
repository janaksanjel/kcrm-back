from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Role, Staff
from .serializers import RoleSerializer, StaffSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('-created_date')
    serializer_class = RoleSerializer

    def get_queryset(self):
        queryset = Role.objects.all().order_by('-created_date')
        mode = self.request.query_params.get('mode')
        if mode:
            queryset = queryset.filter(mode=mode)
        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        mode = request.query_params.get('mode')
        if mode:
            total_roles = Role.objects.filter(mode=mode).count()
            total_staff = Staff.objects.filter(role__mode=mode).count()
            active_staff = Staff.objects.filter(role__mode=mode, is_active=True).count()
        else:
            total_roles = Role.objects.count()
            total_staff = Staff.objects.count()
            active_staff = Staff.objects.filter(is_active=True).count()
        
        return Response({
            'total_roles': total_roles,
            'total_staff': total_staff,
            'active_staff': active_staff
        })

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all().order_by('-created_date')
    serializer_class = StaffSerializer

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        role_id = request.query_params.get('role_id')
        if role_id:
            staff = Staff.objects.filter(role_id=role_id, is_active=True)
            serializer = self.get_serializer(staff, many=True)
            return Response(serializer.data)
        return Response({'error': 'role_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)