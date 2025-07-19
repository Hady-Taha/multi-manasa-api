from rest_framework import serializers
from django.contrib.auth.models import Permission,Group

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['codename', 'name']


class PermissionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name','id']
