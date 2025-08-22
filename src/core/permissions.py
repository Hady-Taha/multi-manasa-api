from rest_framework.permissions import BasePermission,DjangoModelPermissions
from rest_framework.exceptions import PermissionDenied
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

    def has_permission(self, request, view):
        user = request.user
        if (
            user and 
            user.is_authenticated and 
            hasattr(user, 'staff') and 
            user.staff.active
        ):
            return super().has_permission(request, view)
        return False




class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'teacher'):
            raise PermissionDenied("This user is not a teacher.")
        return True


class CustomDjangoModelPermissionsOrIsTeacher(BasePermission):
    """
    Permission that allows access if user has either CustomDjangoModelPermissions OR IsTeacher permission.
    """
    def has_permission(self, request, view):
        # Check if user has CustomDjangoModelPermissions
        custom_perm = CustomDjangoModelPermissions()
        if custom_perm.has_permission(request, view):
            return True
        
        # Check if user is a teacher
        teacher_perm = IsTeacher()
        if teacher_perm.has_permission(request, view):
            return True
        
        return False