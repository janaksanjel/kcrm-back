from rest_framework import serializers
from .models import ReportData

class ReportDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportData
        fields = ['mode', 'report_type', 'data', 'created_at']