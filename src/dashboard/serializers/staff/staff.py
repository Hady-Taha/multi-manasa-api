from rest_framework import serializers
from django.contrib.auth.models import User
from dashboard.serializers.permissions.permissions import PermissionSerializer,PermissionGroupSerializer

class UserWithPermissionSerializer(serializers.ModelSerializer):
    groups = PermissionGroupSerializer(many=True, read_only=True)
    is_admin = serializers.BooleanField(source='staff.is_admin')
    name = serializers.CharField(source='staff.name')
    class Meta:
        model = User
        fields = [
            'name',
            'id', 
            'username', 
            'email', 
            'is_admin',
            'is_superuser',
            'groups'
            ]