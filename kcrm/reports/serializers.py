from rest_framework import serializers
from .models import ReportData

def get_owner_user(request):
    """Helper function to get the owner user (shop owner for staff, or user itself)"""
    try:
        from staff.models import Staff
        staff = Staff.objects.get(user=request.user)
        return staff.shop_owner
    except Staff.DoesNotExist:
        return request.user

class ReportDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportData
        fields = ['mode', 'report_type', 'data', 'created_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            owner_user = get_owner_user(request)
            validated_data['user'] = owner_user
        return super().create(validated_data)