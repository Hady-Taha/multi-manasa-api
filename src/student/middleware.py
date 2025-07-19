from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class StudentBlockMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            auth = JWTAuthentication()
            user, token = auth.authenticate(request)
            
            if user and hasattr(user, 'student') and user.student.block:
                try:
                    outstanding_token = OutstandingToken.objects.get(token=str(token))
                    BlacklistedToken.objects.create(token=outstanding_token)
                    return JsonResponse({"error": "Student Blocked, Logged Out"}, status=403)
                except ObjectDoesNotExist:
                    return JsonResponse({"error": "Invalid Token"}, status=403)
                except Exception:
                    return JsonResponse({"error": "Internal Server Error"}, status=500)

        except (InvalidToken, TokenError):
            return None
        except Exception:
            return None