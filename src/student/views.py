# DJANGO LIB
from django.conf import settings
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
#REST LIB
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
# FILES
from .models import *
from .serializers import StudentProfileSerializer,StudentSignUpSerializer

#* < ==============================[ <- Authentication -> ]============================== > ^#

# SignIn View
class StudentSignInView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate the user with provided credentials
        user = authenticate(username=username, password=password)
        
        # If authentication is successful, generate and return JWT tokens
        if user is not None:
            refresh = RefreshToken.for_user(user)  # Generate refresh token
            access = AccessToken.for_user(user)    # Generate access token
            # Add Header Name To Token
            access_token = f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access}'
            refresh_token = f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {refresh}'

            # Store Token In Student Model
            student = user.student
            student.jwt_token = access_token
            student.save()

            return Response({'refresh_token':refresh_token,'access_token': access_token},status=status.HTTP_200_OK)
        
        # If authentication fails, return an error response
        else:
            return Response({'error': 'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)


# SignUp View
class StudentSignUpView(APIView):
    def post(self, request,*args, **kwargs):

        # Initialize the serializer with the incoming data
        serializer = StudentSignUpSerializer(data=request.data)

        # Validate the data provided by the user
        if serializer.is_valid():
            # Save the valid data, creating a new student instance
            student = serializer.save()
            
            # Generate an access token for the associated user
            access_token = AccessToken.for_user(student.user)

            # Save access_token in model student
            student.jwt_token = f'Bearer {access_token}'
            student.save()

            # Return the access token in the response
            return Response({"access_token": f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access_token}'},status=status.HTTP_200_OK)
        
        # If validation fails, return the errors in the response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

#* < ==============================[ <- Profile  -> ]============================== > ^#

class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        student = get_object_or_404(
            Student.objects.select_related('user', 'education_type', 'year'),
            user=request.user
        )
        res_data = StudentProfileSerializer(student).data
        return Response(res_data, status=status.HTTP_200_OK)
    
