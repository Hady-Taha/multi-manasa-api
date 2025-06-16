import random
import datetime
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
from rest_framework.exceptions import  NotFound
from rest_framework import generics
# FILES
from core.permissions import IsTeacher
from .models import *
from .serializers import *
from course.models import Course
# Create your views here.

#* < ==============================[ <- Authentication -> ]============================== > ^#

# SignIn View
class TeacherSignInView(APIView):
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

            # Store Token In Teacher Model
            teacher = user.teacher
            teacher.jwt_token = access_token
            teacher.save()

            return Response({'refresh_token':refresh_token,'access_token': access_token},status=status.HTTP_200_OK)
        
        # If authentication fails, return an error response
        else:
            return Response({'error': 'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)


# SignUp View
class TeacherSignUpView(APIView):
    def post(self, request,*args, **kwargs):

        # Initialize the serializer with the incoming data
        serializer = TeacherSignUpSerializer(data=request.data)

        # Validate the data provided by the user
        if serializer.is_valid():
            # Save the valid data, creating a new student instance
            teacher = serializer.save()
            
            # Generate an access token for the associated user
            access_token = AccessToken.for_user(teacher.user)

            # Save access_token in model student
            teacher.jwt_token = f'Bearer {access_token}'
            teacher.save()

            # Return the access token in the response
            return Response({"access_token": f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access_token}'},status=status.HTTP_200_OK)
        
        # If validation fails, return the errors in the response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

#* < ==============================[ <- Profile  -> ]============================== > ^#

class TeacherProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        teacher = get_object_or_404(
            Teacher.objects.select_related('user'),
            user=request.user
        )
        res_data = TeacherProfileSerializer(teacher).data
        return Response(res_data, status=status.HTTP_200_OK)
    

#* < ==============================[ <- Course  -> ]============================== > ^#

class CreateCourseView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsAuthenticated,IsTeacher]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacher)


class CoursesListView(generics.ListAPIView):
    serializer_class = CoursesListViewSerializer
    permission_classes = [IsAuthenticated,IsTeacher]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(teacher=user.teacher)
    

class UpdateCourseView(generics.UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'  

    def get_object(self):
        course = super().get_object()
        if course.teacher != self.request.user.teacher:
            raise PermissionDenied("You do not have permission to update this course.")
        return course


class DeleteCourseView(APIView):
    permission_classes = [IsAuthenticated,IsTeacher]

    def delete(self, request, *args, **kwargs):
        user = request.user

        course_id = request.data.get('course_id')
        try:
            course = Course.objects.get(id=course_id, teacher=user.teacher)
        except Course.DoesNotExist:
            raise NotFound("Course not found or you do not have permission to delete it.")
        course.delete()
        return Response({"message": "Course deleted successfully."}, status=status.HTTP_200_OK)