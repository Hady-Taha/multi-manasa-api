from rest_framework.permissions import BasePermission,DjangoModelPermissions
from django.conf import settings

class HasValidAPIKey(BasePermission):

    def has_permission(self, request, view):
        api_key = request.headers.get("api-key")
        valid_api_key = settings.API_KEY_MANASA

        return api_key == valid_api_key
    

class CustomDjangoModelPermissions(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }