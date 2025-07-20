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
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import  NotFound
from rest_framework import generics
# FILES
from core.permissions import IsTeacher
from exam.serializers import ExamSerializer
from exam.models import Exam
from subscription.models import CourseSubscription
from .models import *
from .serializers.profile.profile import *
from .serializers.course.course import *
from .serializers.student.student import*

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


#* < ==============================[ <- Profile -> ]============================== > ^#

class TeacherProfileView(APIView):
    permission_classes = [IsAuthenticated,IsTeacher]

    def get(self, request, *args, **kwargs):
        teacher = get_object_or_404(
            Teacher.objects.select_related('user'),
            user=request.user
        )
        res_data = TeacherProfileSerializer(teacher).data
        return Response(res_data, status=status.HTTP_200_OK)
    


class TeacherCourseCategoryView(generics.ListAPIView):
    serializer_class = TeacherCourseCategorySerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    pagination_class = None
    
    def get_queryset(self):
        return TeacherCourseCategory.objects.filter(teacher=self.request.user.teacher).select_related('course_category')



#* < ==============================[ <- Course -> ]============================== > ^#

#* Course
#list
class TeacherListCourseView(generics.ListAPIView):
    serializer_class = TeacherListCourseSerializer
    permission_classes = [IsAuthenticated,IsTeacher]
    
    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user.teacher)

#create
class TeacherCreateCourseView(generics.CreateAPIView):
    serializer_class = TeacherCreateCourseSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacher)

#update
class TeacherUpdateCourseView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherCreateCourseSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        course = get_object_or_404(Course, id=self.kwargs['id'], teacher=self.request.user.teacher)
        return course

#detail
class TeacherDetailCourseView(generics.RetrieveAPIView):
    serializer_class = TeacherListCourseSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        course = get_object_or_404(Course, id=self.kwargs['id'], teacher=self.request.user.teacher)
        return course

#delete
class TeacherDeleteCourseView(generics.DestroyAPIView):
    serializer_class = TeacherListCourseSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        course = get_object_or_404(Course, id=self.kwargs['id'], teacher=self.request.user.teacher)
        return course


#* Units
#list
class TeacherListUnitView(generics.ListAPIView):
    serializer_class = TeacherListUnitSerializer
    permission_classes = [IsAuthenticated,IsTeacher]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Unit.objects.filter(course__teacher=self.request.user.teacher, course_id=course_id,parent=None)

#create
class TeacherCreateUnitView(generics.CreateAPIView):
    serializer_class = TeacherCreateUnitSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def perform_create(self, serializer):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id, teacher=self.request.user.teacher)
        serializer.save(course=course)

#update
class TeacherUpdateUnitView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherCreateUnitSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        unit = get_object_or_404(Unit, id=self.kwargs['id'], course__teacher=self.request.user.teacher)
        return unit

#delete
class TeacherDeleteUnitView(generics.DestroyAPIView):
    serializer_class = TeacherListUnitSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        unit = get_object_or_404(Unit, id=self.kwargs['id'], course__teacher=self.request.user.teacher)
        return unit



#* Video
#list
class TeacherListVideoView(generics.ListAPIView):
    serializer_class = TeacherListVideoSerializer
    permission_classes = [IsAuthenticated,IsTeacher]
    def get_queryset(self):
        unit_id = self.kwargs['unit_id']
        return Video.objects.filter(unit__course__teacher=self.request.user.teacher, unit_id=unit_id)

#create
class TeacherCreateVideoView(generics.CreateAPIView):
    serializer_class = TeacherCreateVideoSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def perform_create(self, serializer):
        unit_id = self.kwargs['unit_id']
        unit = get_object_or_404(Unit, id=unit_id, course__teacher=self.request.user.teacher)
        serializer.save(unit=unit)
    

#update
class TeacherUpdateVideoView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherCreateVideoSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        video = get_object_or_404(Video, id=self.kwargs['id'], unit__course__teacher=self.request.user.teacher)
        return video


#delete
class TeacherDeleteVideoView(generics.DestroyAPIView):
    serializer_class = TeacherListVideoSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        video = get_object_or_404(Video, id=self.kwargs['id'], unit__course__teacher=self.request.user.teacher)
        return video


# File 
#list
class TeacherListFileView(generics.ListAPIView):
    serializer_class = TeacherListFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        unit_id = self.kwargs['unit_id']
        unit = get_object_or_404(Unit, id=unit_id, course__teacher=self.request.user.teacher)
        return File.objects.filter(unit=unit)

#create
class TeacherCreateFileView(generics.CreateAPIView):
    serializer_class = TeacherCreateFileSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def perform_create(self, serializer):
        unit_id = self.kwargs['unit_id']
        unit = get_object_or_404(Unit, id=unit_id, course__teacher=self.request.user.teacher)
        serializer.save(unit=unit)
    

#update
class TeacherUpdateFileView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherCreateFileSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        file = get_object_or_404(File, id=self.kwargs['id'], unit__course__teacher=self.request.user.teacher)
        return file

#delete
class TeacherDeleteFileView(generics.DestroyAPIView):
    serializer_class = TeacherListFileSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'id'
    
    def get_object(self):
        file = get_object_or_404(File, id=self.kwargs['id'], unit__course__teacher=self.request.user.teacher)
        return file
    
#* < ==============================[ <- Unit Content -> ]============================== > ^#


class UnitContentView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    queryset = Unit.objects.all()

    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Unit, id=unit_id, course__teacher=request.user.teacher)
        content = self.get_content(unit)
        return Response(content, status=status.HTTP_200_OK)

    def get_content(self, unit):
        videos = self.get_videos(unit)
        files = self.get_files(unit)
        subunits = self.get_subunit(unit)
        exams = self.get_exams(unit)

        # Combine and sort videos, files, and exams by 'order'
        combined_content = self.combine_content(videos, files,subunits,exams)
        return combined_content

    def get_videos(self, unit):
        # Retrieve and serialize videos associated with the unit
        videos = unit.unit_videos.all()
        return TeacherListVideoSerializer(videos, many=True).data

    def get_files(self, unit):
        # Retrieve and serialize files associated with the unit
        files = unit.unit_files.all()
        return TeacherListFileSerializer(files, many=True).data

    def get_exams(self, unit):
        # Exams related to  unit
        unit_exams = Exam.objects.filter(unit=unit)
        return ExamSerializer(unit_exams, many=True).data


    def get_subunit(self, unit):
        subunits = unit.subunits.filter(pending=False)
        return TeacherSubunitSerializer(subunits, many=True, context={'request': self.request}).data


    def combine_content(self, videos, files,subunits,exams):
        # Combine videos, files, and exams into a unified list, sorted by 'order'
        combined_content = sorted(
            [{'content_type': 'video', **video} for video in videos] +
            [{'content_type': 'file', **file} for file in files] +
            [{'content_type': 'subunit', **subunit} for subunit in subunits] +
            [{'content_type': 'exam', **exam} for exam in exams] ,
            key=lambda x: x.get('order', 0)
        )
        return combined_content
    

#* < ==============================[ <- Student -> ]============================== > ^#

class TeacherListStudentView(generics.ListAPIView):
    serializer_class = TeacherStudentSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return Student.objects.filter(
            coursesubscription__course__teacher=self.request.user.teacher
        ).distinct()
        



        
class TeacherCenterStudentSignUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        get_code = get_object_or_404(TeacherCenterStudentCode, code=code, is_available=True)
        get_code.student = request.user.student
        get_code.is_available = False
        get_code.save()
        return Response(status=status.HTTP_200_OK)

