# Django lib
import ast
from django.conf import settings
from django.contrib.auth.models import User,Group
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db.models import F, BooleanField, Sum, Case, When, Value,Q,Count,FloatField,Subquery, OuterRef, Q, Exists
from django.db.models.functions import Cast, Coalesce,TruncDate, TruncMonth, TruncYear
from django.db.models import QuerySet
from rest_framework.parsers import JSONParser
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from typing import List, Dict, Any
from django.contrib.auth.models import Permission
from django.db.models import Prefetch
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime,parse_date
from django.db.models.functions import TruncMonth

# RestFrameWork lib
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, filters, status
from rest_framework.filters import SearchFilter,OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from core.permissions import CustomDjangoModelPermissions,IsSuperUser
from core.pagination import CustomPageNumberPagination
from .filters import *
from .utils import copy_unit_to_course

# Apps Models
from student.models import Student,StudentCenterCode,StudentDevice,StudentBlock
from course.models import Course,Unit
from invoice.models import Invoice,InvoiceItemType,InvoicePayStatus,InvoiceMethodPayType,PromoCode
from subscription.models import CourseSubscription,VideoSubscription
from exam.models import Exam,DifficultyLevel, ExamQuestion, ExamType, QuestionType, RandomExamBank, RelatedToChoices, Result, Submission,ExamModel, ExamModelQuestion, TempExamAllowedTimes
from info.models import *
from notification.models import Notification
from .models import RequestLog,Staff
from .tasks import *
from notification.tasks import notifications_custom_send

# Serializers
from .serializers.student.student import *
from .serializers.staff.staff import UserWithPermissionSerializer
from .serializers.course.course import *
from .serializers.invoice.invoice import *
from .serializers.subscription.subscription import ListStudentCourseSubscription
from .serializers.exam.exam import *
from .serializers.info.info_serializers import *
from .serializers.requestlogs.requestlogs import RequestLogSerializer
from .serializers.codes.codes import CourseCodeSerializer,VideoCodeSerializer,StudentCenterCodeSerializer
from .serializers.view.video_views import *
from .serializers.desktop_app.desktop_serializers import *
from .serializers.permissions.permissions import *
from .serializers.analysis.analysis import *
from .serializers.teacher.teacher import *

#ap:Student
#* < ==============================[ <- Student -> ]============================== > ^#

class StudentsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset = Student.objects.select_related('user', 'type_education', 'year').order_by("-created")
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    filterset_class = StudentFilter

    search_fields = [
        'name',
        'code',
        'user__username',
        'parent_phone',
    ]


    ordering_fields = [
        'id',
        'name',
        'created',
        'year',
        'division',
        'block',
        'type_education',
    ]


class StudentUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    serializer_class = UpdateStudentSerializer
    lookup_field = 'id'


class StudentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'id'


class UserDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = User.objects.all()
    lookup_field = 'username'


class UserRestPasswordView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()

    def patch(self , request , username , *args, **kwargs):
        new_password = request.data.get("new_password")
        user = get_object_or_404(User,username=username)

        user.set_password(new_password)
        user.save()

        return Response(status=status.HTTP_200_OK)


class ChangeStudentCenterStatus(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    def patch(self,request,*args, **kwargs):
        student_id = request.data.get("student_id")
        refund_code = request.data.get("refund_code")

        student = get_object_or_404(Student,id=student_id)
        student.is_center = False
        student.save()
        if refund_code:
            get_code = get_object_or_404(StudentCenterCode,code=student.code)
            get_code.student = None
            get_code.available = True
            get_code.save()
            student.code = None
            student.save()
        return Response(status=status.HTTP_200_OK)


class StudentSignCodeView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    
    def post(self,request,*args, **kwargs):
        student_id = request.data.get("student_id")
        code = request.data.get("code")
        student = get_object_or_404(Student,id=student_id)

        # is student edit the code before  
        if student.is_center:
            return Response({"error":"you are can not add your code "},status=status.HTTP_406_NOT_ACCEPTABLE)
        
        try:
            code = StudentCenterCode.objects.get(code=code)
            
            # if the code is already taken 
            if code.available == False:
                return Response({"error":"this code is already taken"},status=status.HTTP_406_NOT_ACCEPTABLE)
            
            # else sign code to student and make student is_center = True
            # update code
            code.available = False
            code.student=student
            # update student
            student.is_center = True
            student.code = code.code
            # saves
            code.save()
            student.save()
        
        except StudentCenterCode.DoesNotExist:
            return Response({"error":"This Code Does Not Exist"},status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_201_CREATED)


class StudentPointListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentPoint.objects.all().order_by("-created")
    serializer_class = StudentPointSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = [
        'student',
        'point_type',
        'created',
    ]
    
    search_fields = [
        'student__name',
        'student__code',
        'student__user__username',
        'points_note',
        ]


class StudentLoginSessionView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentLoginSession.objects.all().order_by('-created')
    serializer_class = StudentLoginSessionSerializer
    filterset_fields = [
            'student_id',
        ]


class StudentBlockCreateView(APIView):
    permission_classes=[IsAuthenticated,CustomDjangoModelPermissions]
    queryset = StudentBlock.objects.all()

    def post(self,request,*args, **kwargs):
        student_id = request.data.get("student_id")
        reason = request.data.get("reason")
        get_student=Student.objects.get(id=student_id)
        get_student.block = True
        get_student.save()
        StudentBlock.objects.create(student=get_student,staff=request.user.staff,reason=reason)
        return Response({"massage":"done"},status=status.HTTP_200_OK)
    

class StudentBlockListView(generics.ListAPIView):
    permission_classes=[IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = StudentBlockSerializer
    queryset = StudentBlock.objects.all()
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    
    filterset_fields = [
            'student__user__username',
        ]

    search_fields = [
        'student__name',
        'staff__name',
        'reason',
    ]


class StudentDeviceListView(generics.ListAPIView):
    permission_classes=[IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = StudentDeviceSerializer
    queryset = StudentDevice.objects.all()
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    filterset_fields = [
        'student_id',
        'device_id',
    ]


class StudentDeviceDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentDevice.objects.all()
    lookup_field = 'id'  # Adjust if your lookup is by another field
    serializer_class = StudentDeviceSerializer

#ap:Staff
#* < ==============================[ <- Staff -> ]============================== > *#

class CreateStaffView(APIView):
    permission_classes = [IsSuperUser]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        name = request.data.get("name")

        if not username or not password or not email:
            return Response(
                {"error": "Username, password, and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_staff=True
        )
        student = Student.objects.create(
            user= user,
            name = name,
            parent_phone = "admin",
            type_education_id = 1,
            year_id = 3,
            government = "admin",
            jwt_token = "admin",
            active = 1,
            is_admin = 1,
        )

        # Create corresponding Staff profile
        staff = Staff.objects.create(
            user=user,
            name=name,
            jwt_token="generated_token_if_any",  # Replace with real token logic if needed
            active=True,
            is_admin=True  # or False depending on your logic
        )


        return Response(
            {"message": "User created successfully", "username": user.username},
            status=status.HTTP_201_CREATED,
        )
    

class StaffListView(generics.ListAPIView):
    permission_classes = [IsSuperUser]
    queryset = User.objects.filter(is_staff=True)
    serializer_class = UserWithPermissionSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = ['username']


class StaffProfileView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_staff:
            serializer = UserWithPermissionSerializer(user)
            return Response(serializer.data)
        return Response(status=status.HTTP_502_BAD_GATEWAY)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = UserWithPermissionSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffSignInView(APIView):
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate the user with provided credentials
        user = authenticate(username=username, password=password)

        # If authentication is successful, generate and return JWT tokens
        if user is not None:
            refresh = RefreshToken.for_user(user)  # Generate refresh token
            access = AccessToken.for_user(user)    # Generate access token

            # Add Header Name To Token
            access_token = f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access}'
            refresh_token = f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {refresh}'
            
            # staff Token In Student Model
            staff = user.staff
            staff.jwt_token = access_token
            staff.save()
            context = {
                    'refresh_token':refresh_token,
                    'access_token': access_token
                }
            
            return Response(context,status=status.HTTP_200_OK)

        # If authentication fails, return an error response
        else:
            context = {
                'error': 'Invalid Credentials', 
            }

            return Response(context,status=status.HTTP_400_BAD_REQUEST)



#* < ==============================[ <- Permissions -> ]============================== > *#

class PermissionGroupListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    queryset = Group.objects.all()
    pagination_class = None
    serializer_class = PermissionGroupSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]


class AssignGroupToUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        user_id = request.data.get("user_id")
        group_ids = request.data.get("group_ids")  # Expecting a list

        if not isinstance(group_ids, list):
            return Response({'detail': 'group_ids must be a list of group IDs.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        groups = Group.objects.filter(id__in=group_ids)
        if not groups.exists():
            return Response({'detail': 'No valid groups found for the given IDs.'}, status=status.HTTP_404_NOT_FOUND)

        user.groups.add(*groups)  # Add multiple groups at once

        return Response({
            'detail': f"Groups assigned to user '{user.username}'.",
            'groups': [group.name for group in groups]
        }, status=status.HTTP_200_OK)
    



#ap:Teacher
#* < ==============================[ <- Teacher -> ]============================== > ^#

class TeacherListView(generics.ListAPIView):
    queryset = Teacher.objects.all().order_by("-created")
    serializer_class = TeacherListSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [
        'id',
        'name',
        'government',
        'active',
        'teacher_course_categories__course_category',
    ]
    search_fields = ['name','user__username']


class TeacherSimpleListView(APIView):
    def get(self, request, *args, **kwargs):
        course_category_id = request.GET.get('course_category_id')
        
        if course_category_id:
            teacher_ids = TeacherCourseCategory.objects.filter(
                course_category_id=course_category_id
            ).values_list('teacher_id', flat=True)
            queryset = Teacher.objects.filter(id__in=teacher_ids).values('id', 'name')
        else:
            queryset = Teacher.objects.all().values('id', 'name')
        
        return Response(queryset, status=status.HTTP_200_OK)


class TeacherCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Teacher.objects.all()
    
    def post(self, request):

        serializer = TeacherCreateSerializer(data=request.data)

        if serializer.is_valid():
            # Save the valid data, creating a new teacher instance
            teacher = serializer.save()

            # Generate an access token for the associated user
            access_token = AccessToken.for_user(teacher.user)

            # Save access_token in model teacher
            teacher.jwt_token = f'Bearer {access_token}'
            teacher.save()

            # Return the access token in the response
            context = {
                "access_token": f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access_token}'
            }

            return Response(context,status=status.HTTP_200_OK)
        
        # If validation fails, return the errors in the response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Teacher.objects.all()
    serializer_class = TeacherUpdateSerializer
    lookup_field = 'id'


class TeacherDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Teacher.objects.all()
    serializer_class = TeacherListSerializer
    lookup_field = 'id'
    


#ap:Course
#* < ==============================[ <- CourseCategory -> ]============================== > ^#


class CourseCategoryListView(generics.ListAPIView):
    queryset = CourseCategory.objects.all().order_by("-created")
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [
        'id',
        'name'
        ]
    search_fields = ['name']

class CourseCategoryListSimpleView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        qr = CourseCategory.objects.values("id", "name",)

        return Response(qr, status=status.HTTP_200_OK)


class CourseCategoryCreateView(generics.CreateAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

class CourseCategoryUpdateView(generics.UpdateAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    lookup_field = 'id'

class CourseCategoryDeleteView(generics.DestroyAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    lookup_field = 'id'


#* < ==============================[ <- Course -> ]============================== > *#

class CourseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset = Course.objects.all().order_by("-created")
    serializer_class = ListCourseSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    filterset_fields = [
        'teacher',
        'id',
        'year',
        'pending',
        'is_center',
        'category',
        'can_buy',
        'created',
        'type_education',
        ]

    search_fields = ['name','description',]


class CourseDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Course.objects.all() 
    serializer_class = ListCourseSerializer
    lookup_field = 'id'


class CourseCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateCourseSerializers
    queryset = Course.objects.all()


class CourseUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]  
    queryset = Course.objects.all()
    serializer_class = CreateCourseSerializers
    lookup_field = 'id'


class CourseDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Course.objects.all()
    serializer_class = ListCourseSerializer
    lookup_field = 'id'


class CourseListSimple(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        year_id = request.query_params.get('year_id')
        qr = Course.objects.values("id", "name",'price')
        
        if year_id:
            qr = qr.filter(year_id=year_id)

        return Response(qr, status=status.HTTP_200_OK)



#* < ==============================[ <- Unit -> ]============================== > *#


class UnitListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListUnitSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['pending']
    search_fields = ['name', 'description']

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Unit.objects.filter(course_id=course_id,parent=None).order_by("order")
    


class UnitCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateUnitSerializer
    queryset = Unit.objects.all()

    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        serializer.save(course=course)



class UnitUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateUnitSerializer
    queryset = Unit.objects.all()
    def get_object(self):
        unit_id = self.kwargs.get('unit_id')
        return get_object_or_404(Unit, id=unit_id)
    

class UnitDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListUnitSerializer
    queryset = Unit.objects.all()
    
    def get_object(self):
        unit_id = self.kwargs.get('unit_id')
        return get_object_or_404(Unit, id=unit_id)
    

class UnitContentView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Unit.objects.all()

    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Unit, id=unit_id)
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
        return ListVideoSerializer(videos, many=True).data

    def get_files(self, unit):
        # Retrieve and serialize files associated with the unit
        files = unit.unit_files.all()
        return ListFileSerializer(files, many=True).data

    def get_exams(self, unit):
        # Exams related to  unit
        unit_exams = Exam.objects.filter(unit=unit)
        return ExamSerializer(unit_exams, many=True).data


    def get_subunit(self, unit):
        subunits = unit.subunits.filter(pending=False)
        return SubunitSerializer(subunits, many=True, context={'request': self.request}).data


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



class UnitResortView(APIView):
    def post(self, request, *args, **kwargs):
        units_data = request.data

        if not isinstance(units_data, list) or not units_data:
            return Response({'detail': 'Expected a non-empty list of units.'}, status=status.HTTP_400_BAD_REQUEST)

        # Preload all units and validate
        unit_ids = [unit.get('id') for unit in units_data]
        units = Unit.objects.filter(id__in=unit_ids)

        if units.count() != len(unit_ids):
            return Response({'detail': 'One or more units not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure all units have the same parent and course
        parents = set(unit.parent_id for unit in units)
        courses = set(unit.course_id for unit in units)

        if len(parents) > 1 or len(courses) > 1:
            return Response({'detail': 'All units must belong to the same course and parent (subunit group).'}, status=status.HTTP_400_BAD_REQUEST)

        # Reorder
        with transaction.atomic():
            for unit_data in units_data:
                unit_id = unit_data.get('id')
                new_order = unit_data.get('order')

                if unit_id is None or new_order is None:
                    return Response({'detail': 'Each unit must have id and order.'}, status=status.HTTP_400_BAD_REQUEST)

                unit = next((u for u in units if u.id == unit_id), None)
                if unit:
                    unit.order = new_order
                    unit.save()

        return Response({'detail': 'Units reordered successfully.'}, status=status.HTTP_200_OK)


class SubunitResortView(APIView):
    def post(self, request, *args, **kwargs):
        units_data = request.data

        if not isinstance(units_data, list) or not units_data:
            return Response({'detail': 'Expected a non-empty list of subunits.'}, status=status.HTTP_400_BAD_REQUEST)

        unit_ids = [unit.get('id') for unit in units_data]
        order_values = [unit.get('order') for unit in units_data]

        if None in unit_ids or None in order_values:
            return Response({'detail': 'Each subunit must have both "id" and "order".'}, status=status.HTTP_400_BAD_REQUEST)

        if len(order_values) != len(set(order_values)):
            return Response({'detail': 'Duplicate order values are not allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        units = Unit.objects.filter(id__in=unit_ids)

        if units.count() != len(unit_ids):
            return Response({'detail': 'One or more subunits not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure all are subunits (have a parent) and share the same parent
        parents = set(unit.parent_id for unit in units)

        if None in parents:
            return Response({'detail': 'Top-level units are not allowed in this view. Only subunits are allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(parents) > 1:
            return Response({'detail': 'All subunits must have the same parent.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for unit_data in units_data:
                unit_id = unit_data['id']
                new_order = unit_data['order']

                unit = next((u for u in units if u.id == unit_id), None)
                if unit:
                    unit.order = new_order
                    unit.save()

        return Response({'detail': 'Subunits reordered successfully.'}, status=status.HTTP_200_OK)



class UnitCopyView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication

    def post(self, request, *args, **kwargs):
        source_unit_id = request.data.get('source_unit_id')
        target_course_id = request.data.get('target_course_id')
        new_unit_name = request.data.get('new_unit_name')
        
        # Call the copy function
        new_unit = copy_unit_to_course(source_unit_id, target_course_id, new_unit_name)
        return Response(
            {
                'message': 'Unit copied successfully',
                'new_unit_id': new_unit.id,
                'new_unit_name': new_unit.name,
                'target_course_id': target_course_id,
            },
            status=status.HTTP_201_CREATED
        )


class UnitListSimple(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,course_id,*args, ** kwargs):
        qr = Unit.objects.filter(course_id=course_id).values("id",'name')
        return Response(qr,status=status.HTTP_200_OK)


#* < ==============================[ <- Content -> ]============================== > *#

#* Video
class VideoListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListVideoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['pending']
    search_fields = ['name', 'description']
    queryset = Video.objects.all()

    def get_queryset(self):
        unit_id = self.kwargs.get('unit_id')
        return Video.objects.filter(unit=unit_id)


class VideoCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateVideoSerializer
    queryset = Video.objects.all() 

    def perform_create(self, serializer):
        unit_id = self.kwargs.get('unit_id')
        unit = get_object_or_404(Unit, id=unit_id)
        serializer.save(unit=unit)


class VideoUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Video.objects.all()
    serializer_class = CreateVideoSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

    def get_object(self):
        video_id = self.kwargs.get('video_id')
        return get_object_or_404(Video, id=video_id)
    

class VideoDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListVideoSerializer
    queryset = Video.objects.all()

    def get_object(self):
        video_id = self.kwargs.get('video_id')
        return get_object_or_404(Video, id=video_id)
    
#* Video File
class VideoFileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = FileVideoSerializer 
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    def get_queryset(self):
        video_id = self.kwargs['video_id']
        return VideoFile.objects.filter(video=video_id)
    

class VideoFileCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = FileVideoSerializer
    queryset = VideoFile.objects.all()

    def perform_create(self, serializer):
        video_id = self.kwargs.get('video_id')
        video = get_object_or_404(Video, id=video_id)
        serializer.save(video=video)


class VideoFileDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = FileVideoSerializer
    queryset = VideoFile.objects.all()

    def get_object(self):
        file_id = self.kwargs.get('file_id')
        return get_object_or_404(VideoFile, id=file_id)
    

class VideoSimpleList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,unit_id,*args, ** kwargs):
        qr = Video.objects.filter(unit_id=unit_id).values("id",'name','price')
        return Response(qr,status=status.HTTP_200_OK)


#* File
class FileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListFileSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['pending']
    search_fields = ['name']
    
    def get_queryset(self):
        unit_id = self.kwargs['unit_id']
        return File.objects.filter(unit=unit_id)
    

class FileCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateFileSerializer
    queryset = File.objects.all()

    def perform_create(self, serializer):
        unit_id = self.kwargs.get('unit_id')
        unit = get_object_or_404(Unit, id=unit_id)
        serializer.save(unit=unit)


class FileDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListFileSerializer
    queryset = File.objects.all()

    def get_object(self):
        file_id = self.kwargs.get('file_id')
        return get_object_or_404(File, id=file_id)
    
#* Content Details
class ContentDetailsView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Unit.objects.all()

    def get(self, request, content_type, content_id, *args, **kwargs):

        # Handle content access
        if content_type == "video":
            return self.video_details(content_id)
        elif content_type == "file":
            return self.file_details(content_id)
        else:
            return Response({"error": "Invalid content type"},status=status.HTTP_400_BAD_REQUEST,)

    def video_details(self, video_id):
        video = get_object_or_404(Video, id=video_id)
        return Response(ListVideoSerializer(video).data, status=status.HTTP_200_OK)

    def file_details(self, file_id):
        file = get_object_or_404(File, id=file_id)
        return Response(ListFileSerializer(file).data, status=status.HTTP_200_OK)
    


class ContentResortView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Course.objects.all()

    def post(self, request, *args, **kwargs):
        content_list = request.data

        for content in content_list:
            content_type = content.get('content_type')
            object_id = content.get('id')
            new_order = content.get('order')

            if not (content_type and object_id and new_order is not None):
                return Response({'detail': 'Invalid data.'}, status=status.HTTP_400_BAD_REQUEST)

            if content_type == 'video':
                obj = get_object_or_404(Video, id=object_id)
            elif content_type == 'file':
                obj = get_object_or_404(File, id=object_id)
            elif content_type == 'exam':
                obj = get_object_or_404(Exam, id=object_id)
            elif content_type == 'unit':
                obj = get_object_or_404(Unit, id=object_id)
            elif content_type == 'subunit':
                obj = get_object_or_404(Unit, id=object_id)
            else:
                return Response({'detail': f'Unknown content_type: {content_type}'}, status=status.HTTP_400_BAD_REQUEST)

            obj.order = new_order
            obj.save()

        return Response({'detail': 'Order updated successfully.'}, status=status.HTTP_200_OK)


#ap:Codes
#* < ==============================[ <- CODES -> ]============================== > ^#

#* Course Code
class CodeCourseGenerate(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseCode.objects.all()

    def post(self, request, *args, **kwargs):
        title = request.data.get("title")
        course_id = request.data.get("course_id")  # Optional
        price = request.data.get("price")
        quantity = int(request.data.get("quantity", 0))

        if quantity <= 0:
            return Response({"detail": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id) if course_id else None
        except Course.DoesNotExist:
            return Response({"error": "Invalid course_id."}, status=status.HTTP_400_BAD_REQUEST)

        if not price:
            return Response({"error": "Price is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch all existing codes
        existing_codes = set(CourseCode.objects.values_list("code", flat=True))
        codes_set = set()
        codes_to_create = []

        # Generate unique numeric codes
        while len(codes_set) < quantity:
            number = '1' + ''.join(random.choices('0123456789', k=10))  # 11-digit
            if number not in existing_codes and number not in codes_set:
                codes_set.add(number)
                codes_to_create.append(CourseCode(
                    code=number,
                    title=title,
                    course=course,
                    price=price
                ))

        # Bulk insert
        with transaction.atomic():
            CourseCode.objects.bulk_create(codes_to_create, batch_size=10000)

        return Response({
            "message": f"{quantity} course codes generated successfully.",
            "codes": list(codes_set)
        }, status=status.HTTP_201_CREATED)


class CodeCourseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseCode.objects.all().order_by("-created")
    serializer_class = CourseCodeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [
        'course__teacher',
        'course',
        'available'
        ]
    search_fields = ['title', 'code','student__user__username']


#* Video Code
class CodeVideoGenerate(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = VideoCode.objects.all()

    def post(self, request, *args, **kwargs):
        title = request.data.get("title")
        course_id = request.data.get("course_id")
        video_id = request.data.get("video_id")  # Optional
        price = request.data.get("price")
        quantity = int(request.data.get("quantity", 0))

        if quantity <= 0:
            return Response({"detail": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate course
        if not course_id:
            return Response({"error": "course_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Invalid course_id."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate video (optional)
        video = None
        if video_id:
            try:
                video = Video.objects.get(id=video_id)
            except Video.DoesNotExist:
                return Response({"error": "Invalid video_id."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate price
        if not price:
            return Response({"error": "Price is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Get existing codes
        existing_codes = set(VideoCode.objects.values_list("code", flat=True))
        codes_set = set()
        codes_to_create = []

        # Generate unique numeric codes
        while len(codes_set) < quantity:
            number = '2' + ''.join(random.choices('0123456789', k=10))
            if number not in existing_codes and number not in codes_set:
                codes_set.add(number)
                codes_to_create.append(
                    VideoCode(
                        code=number,
                        title=title,
                        course=course,
                        video=video,
                        price=price
                    )
                )

        # Bulk insert
        with transaction.atomic():
            VideoCode.objects.bulk_create(codes_to_create, batch_size=10000)

        return Response(
            {"codes": list(codes_set)},
            status=status.HTTP_201_CREATED
        )


class CodeVideoListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = VideoCodeSerializer
    queryset = VideoCode.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['course','available']
    search_fields = ['title', 'code','student__user__username']



#* Student Code
class GenerateTeacherCenterStudentCodes(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = TeacherCenterStudentCode.objects.all()
        
    def post(self, request, *args, **kwargs):
        quantity = int(request.data.get("quantity", 0))
        teacher = get_object_or_404(Teacher, id=request.data.get("teacher_id"))

        if quantity <= 0:
            return Response({"detail": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

        existing_codes = set(
            TeacherCenterStudentCode.objects.values_list("code", flat=True)
        )
        codes_set = set()
        codes_to_create = []

        # Generate unique numeric codes
        while len(codes_set) < quantity:
            number = '00' + ''.join(random.choices('0123456789', k=6))
            if number not in existing_codes and number not in codes_set:
                codes_set.add(number)
                codes_to_create.append(
                    TeacherCenterStudentCode(teacher=teacher, code=number)
                )

        # Bulk insert
        with transaction.atomic():
            TeacherCenterStudentCode.objects.bulk_create(codes_to_create, batch_size=10000)

        return Response({"codes": list(codes_set)}, status=status.HTTP_201_CREATED)


class StudentTeacherCenterCodesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = TeacherCenterStudentCode.objects.all().order_by("-created")
    serializer_class = TeacherCenterStudentCodeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [
        'id',
        'available',
        ]
    search_fields = [
        'student__user__username',
        'code',
        'id',
        'student__name',
        ]


#ap:Invoice
#* < ==============================[ <- Invoice -> ]============================== > ^#

class InvoiceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListInvoiceSerializer
    queryset = Invoice.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = InvoiceFilter
    search_fields = [
        'teacher',
        'student__user__username', 
        'sequence',
        'item_barcode',
        'item_name',
        'promo_code__code',
        ]
    

class UpdateInvoicePayStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Invoice.objects.all()
    serializer_class = UpdateInvoiceSerializer
    lookup_field = 'id'  


class CreateInvoiceManually(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Invoice.objects.all()

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        barcode = request.data.get("barcode")

        # Fetch the student and course or return 404 if not found
        get_student = get_object_or_404(Student, user__username=username)
        get_course = get_object_or_404(Course, barcode=barcode)

        
        # Check if an invoice with the same student and course already exists and is paid
        is_invoice_pay_exists = Invoice.objects.filter(student=get_student, item_barcode=get_course.barcode, pay_status=InvoicePayStatus.PAID).exists()
        if is_invoice_pay_exists:
            return Response({"invoice_pay_exists": is_invoice_pay_exists}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate price and set expiration time
        expires_at = timezone.now()
        price = get_course.price

        # Create the invoice record
        create_invoice = Invoice.objects.create(
            student=get_student,
            pay_status=InvoicePayStatus.PAID,
            pay_method=InvoiceMethodPayType.MANUALLY,
            amount=get_course.price,
            pay_at=timezone.now(),
            expires_at=timezone.now(),
            item_type=InvoiceItemType.COURSE,
            item_barcode=get_course.barcode,
            item_name=get_course.name,
            item_price = get_course.price,
        )
        
        # Return the invoice sequence in the response
        return Response({"sequence": create_invoice.sequence}, status=status.HTTP_200_OK)


#PromoCode
class ListPromoCode(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset =  PromoCode.objects.all().order_by("-created")
    serializer_class = ListPromoCodeSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    filterset_fields = [
            'course',
            'usage_limit',
            'used_count',
            'is_active',
            ]

    search_fields = [
        'code',
        ]



class CreatePromoCode(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = PromoCode.objects.all()
    serializer_class = ListPromoCodeSerializer



class UpdatePromoCode(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = PromoCode.objects.all()
    serializer_class = ListPromoCodeSerializer
    lookup_field = 'id'  



#ap:Subscription
#* < ==============================[ <- Subscription -> ]============================== > ^#

class CourseSubscriptionList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all().order_by("-created")
    serializer_class = ListStudentCourseSubscription
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    search_fields = [
        'student__name',
        'student__user__username',
        'course__name',
        'invoice__sequence',
        ]

    filterset_fields = [
            'student__year',
            'student',
            'course__teacher',
            'course',
            'active',
            'student__government'
        ]


class CancelSubscription(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all()

    def post(self,request,*args, **kwargs):
        subscription_id = request.data.get("subscription_id")
        get_subscription = get_object_or_404(CourseSubscription,id=subscription_id)
        get_subscription.active = False
        get_subscription.save()
        return Response(status=status.HTTP_200_OK)


class CancelSubscriptionBulk(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all()

    def post(self,request,*args, **kwargs):
        student_id = request.data.get("student_id")
        get_subscriptions = CourseSubscription.objects.filter(student_id=student_id)
        get_subscriptions.update(active=False)
        return Response(status=status.HTTP_200_OK)


class SubscriptionStartBulk(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all()
    
    def post(self, request, *args, **kwargs):
        students_list = request.data.get("students", [])
        course_id = request.data.get("course_id")

        skipped_students = []

        for student in students_list:
            try:
                get_student = Student.objects.get(Q(user__username=student) | Q(code=student))
                CourseSubscription.objects.get_or_create(
                    student=get_student,
                    course_id=course_id,
                    active=True
                )
            except Student.DoesNotExist:
                skipped_students.append(student)

        return Response({"skipped_students": skipped_students}, status=status.HTTP_200_OK)


class RenewSubscription(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all()

    def post(self,request,*args, **kwargs):
        subscription_id = request.data.get("subscription_id")
        subscription = get_object_or_404(CourseSubscription, id=subscription_id)
        subscription.active = True
        subscription.save()
        return Response(status=status.HTTP_200_OK) 

#ap:View
#* < ==============================[ <- View -> ]============================== > ^#

class VideoViewList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = VideoView.objects.filter(counter__gte = 1).order_by("-created")
    serializer_class = ListVideoViewListSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    search_fields = [
        'student__user__username',
        'student__name',
    ]
    filterset_fields = [
        'student',
        'student__year',
        'counter',
        'video',
        'video__unit__course',
    ]


class UpdateStudentView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = VideoView.objects.all()

    def patch(self,request,view_id,*args, **kwargs):

        counter_amount = request.data.get("counter_amount")

        view = get_object_or_404(VideoView,id=view_id)
        view.counter = int(counter_amount)
        view.save()

        return Response(status=status.HTTP_200_OK)


class StudentsNotViewedVideo(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = VideoView.objects.all()

    def get(self, request, video_id, *args, **kwargs):
        # Get the video or return a 404 error if not found
        video = get_object_or_404(Video, id=video_id)

        # Get IDs of students subscribed to the course and active
        subscribed_students = CourseSubscription.objects.filter(
            course=video.unit.course, active=True
        ).values_list('student_id', flat=True)

        # Filter students who have not viewed the video (counter < 1 or no entry in VideoView)
        not_viewed_students = Student.objects.filter(id__in=subscribed_students).exclude(
            id__in=VideoView.objects.filter(
                video=video, counter__gte=1
            ).values_list('student_id', flat=True)
        )

        # Paginate the data
        paginator = CustomPageNumberPagination()
        paginated_students = paginator.paginate_queryset(not_viewed_students, request)

        # Serialize the data
        serializer = StudentSerializer(paginated_students, many=True)

        return paginator.get_paginated_response(serializer.data)


class VideoViewSessionsList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ViewSession.objects.all().order_by("-created")
    serializer_class = ViewSessionListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'session',
        'view__student__user__username',
    ]
    filterset_class = ViewSessionFilter  


#ap:Info
#* < ==============================[ <- Info -> ]============================== > ^#

class TeacherInfoListView(generics.ListAPIView):
    queryset = TeacherInfo.objects.all()
    serializer_class = TeacherInfoSerializer
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]


# Centers
class CenterListView(generics.ListAPIView):
    queryset = Center.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = CenterSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=['government','id']
    search_fields=['name']

class CenterCreateView(generics.CreateAPIView):
    queryset = Center.objects.all()
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = CenterSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]

class CenterUpdateView(generics.UpdateAPIView):
    queryset = Center.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CenterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = []
    search_fields = []
    lookup_field = 'id' 

class CenterDeleteView(generics.DestroyAPIView):
    queryset = Center.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CenterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = []
    search_fields = []
    lookup_field = 'id'

# Timing Center
class TimingCenterListView(generics.ListAPIView):
    queryset = TimingCenter.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = TimingCenterSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[
        'year',
        'is_available',
    ]
    search_fields=[
        'day',
    ]

    def get_queryset(self):
        center_id = self.kwargs['center_id']
        return TimingCenter.objects.filter(center_id=center_id)

class TimingCenterCreateView(generics.CreateAPIView):
    queryset = TimingCenter.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = TimingCenterSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]

class TimingCenterUpdateView(generics.UpdateAPIView):
    queryset = TimingCenter.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = TimingCenterSerializer
    lookup_field = 'id'

class TimingCenterDeleteView(generics.DestroyAPIView):
    queryset = TimingCenter.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = TimingCenterSerializer
    lookup_field = 'id'


# Books
class BookListView(generics.ListAPIView):
    queryset = Book.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]

class BookCreateView(generics.CreateAPIView):
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]

class BookUpdateView(generics.UpdateAPIView):
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = []
    search_fields = []
    lookup_field = 'id'

class BookDeleteView(generics.DestroyAPIView):
    
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = []
    search_fields = []
    lookup_field = 'id'


# Distributor
class DistributorListView(generics.ListAPIView):
    queryset = Distributor.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = DistributorSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]

class DistributorCreateView(generics.CreateAPIView):
    queryset = Distributor.objects.all()
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = DistributorSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]

class DistributorUpdateView(generics.UpdateAPIView):
    queryset = Distributor.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = DistributorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = []
    search_fields = []
    lookup_field = 'id'

class DistributorDeleteView(generics.DestroyAPIView):
    queryset = Distributor.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = DistributorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = []
    search_fields = []
    lookup_field = 'id'

# Distributor Book
class DistributorBookListView(generics.ListAPIView):
    queryset = DistributorBook.objects.all().order_by("-created")
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    serializer_class = DistributorBookSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields=[]
    search_fields=[]

    def get_queryset(self):
        distributor_id = self.kwargs['distributor_id']
        return DistributorBook.objects.filter(distributor_id=distributor_id)

class DistributorBookAddView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = DistributorBook.objects.all().order_by("-created")

    def post(self, request, distributor_id, *args, **kwargs):
        distributor = get_object_or_404(Distributor, id=distributor_id)
        books_ids = request.data.get("books_ids", [])

        # Get existing book IDs already assigned to the distributor
        existing_book_ids = set(
            DistributorBook.objects.filter(distributor=distributor, book_id__in=books_ids)
            .values_list("book_id", flat=True)
        )

        # Filter out existing ones
        new_book_ids = [book_id for book_id in books_ids if book_id not in existing_book_ids]

        distributor_books = [
            DistributorBook(distributor=distributor, book_id=book_id)
            for book_id in new_book_ids
        ]
        DistributorBook.objects.bulk_create(distributor_books)

        return Response(
            {
                "message": f"{len(distributor_books)} new books added to distributor.",
                "skipped": list(existing_book_ids),
            },
            status=status.HTTP_201_CREATED
        )

class DistributorBookAvailabilityUpdateView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = DistributorBook.objects.all().order_by("-created")

    def patch(self, request, distributor_id, *args, **kwargs):
        distributor = get_object_or_404(Distributor, id=distributor_id)
        books_ids = request.data.get("books_ids", [])
        is_available = request.data.get("is_available")

        updated_count = DistributorBook.objects.filter(
            distributor=distributor,
            book_id__in=books_ids
        ).update(is_available=is_available)

        return Response(
            {"message": f"{updated_count} books updated to is_available={is_available}."},
            status=status.HTTP_200_OK
        )

class DistributorBookDeleteView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = DistributorBook.objects.all().order_by("-created")

    def delete(self, request, distributor_id, *args, **kwargs):
        distributor = get_object_or_404(Distributor, id=distributor_id)
        books_ids = request.data.get("books_ids", [])


        deleted_count, _ = DistributorBook.objects.filter(
            distributor=distributor,
            book_id__in=books_ids
        ).delete()

        return Response(
            {"message": f"{deleted_count} books removed from distributor."},
            status=status.HTTP_200_OK
        )

#ap:Logs
#* < ==============================[ <- Logs -> ]============================== > ^#

class RequestLogListView(generics.ListAPIView):
    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = RequestLogFilter 
    search_fields = ['path', 'view_name']
    ordering_fields = ['timestamp', 'response_time', 'status_code']
    ordering = ['-timestamp']

class RequestLogDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date and not end_date:
            return Response(
                {"error": "At least one of start_date or end_date must be provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start building the query
        query_filter = {}
        
        # Process start_date if provided
        if start_date:
            try:
                # Try to parse as ISO datetime first
                start_datetime = parse_datetime(start_date)
                
                # If that fails, try to parse as date only
                if not start_datetime:
                    date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                    start_datetime = timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time.min))
                
                # If it's still None, it's an invalid format
                if not start_datetime:
                    return Response(
                        {"error": "Invalid start_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                query_filter['timestamp__gte'] = start_datetime
                
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Process end_date if provided
        if end_date:
            try:
                # Try to parse as ISO datetime first
                end_datetime = parse_datetime(end_date)
                
                # If that fails, try to parse as date only
                if not end_datetime:
                    date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                    end_datetime = timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time.max))
                
                # If it's still None, it's an invalid format
                if not end_datetime:
                    return Response(
                        {"error": "Invalid end_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                query_filter['timestamp__lte'] = end_datetime
                
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Debug info before deletion
        logs_before_delete = RequestLog.objects.filter(**query_filter).count()
        
        # Delete logs
        deleted, _ = RequestLog.objects.filter(**query_filter).delete()
        
        # Add debug info to response
        return Response({
            "message": f"Successfully deleted {deleted} logs",
            "deleted_count": deleted,
            "found_before_delete": logs_before_delete,
            "query_filter": {
                "start_date": str(query_filter.get('timestamp__gte')),
                "end_date": str(query_filter.get('timestamp__lte'))
            }
        })



#ap:CenterApp
#* < ==============================[ <- CenterApp -> ]============================== > ^#

class ExamCenterList(generics.ListAPIView):
    queryset = ExamCenter.objects.all()
    serializer_class = ExamCenterSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['id','date','year']
    search_fields = ['name', 'lecture']


class ResultExamCenterList(generics.ListAPIView):
    queryset = ResultExamCenter.objects.all()
    serializer_class = ResultExamCenterSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['exam','student','exam__date','updated','created']
    search_fields = ['student__code','student__user__username','student__id','student__parent_phone']


#ap:Analysis
#* < ==============================[ <- Analysis -> ]============================== > ^#

#Invoices
class InvoiceChartData(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset=Invoice.objects.all()
    
    def get(self, request, *args, **kwargs):
        serializer = InvoiceChartFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        chart_data = serializer.get_chart_data()
        return Response(chart_data)





#ap:Notification
#* < ==============================[ <- Notification -> ]============================== > ^#

class NotificationCreateView(APIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset = Notification.objects.all()
    
    def post(self,request,*args, **kwargs):
        notify_type = request.data.get("notify_type") 
        notify_id = request.data.get("notify_id")
        notify_text = request.data.get("text")
        
        if notify_type == 'course':
            self.notify_course_subscriptions(notify_id,notify_text)
        
        elif notify_type =='year':
            self.notify_year(notify_id,notify_text)
        
        
        return Response(status=status.HTTP_200_OK)


    def notify_course_subscriptions(self,course_id,notify_text):
        get_course = Course.objects.get(id=course_id)
        get_student_ids = Student.objects.filter(coursesubscription__course=get_course,coursesubscription__active=True).values_list("id",flat=True)
        notifications_custom_send.delay(list(get_student_ids),notify_text)


    def notify_year(self,year_id,notify_text):
        get_year=Year.objects.get(id=year_id)
        get_student_ids = Student.objects.filter(year=get_year).values_list("id",flat=True)
        notifications_custom_send.delay(list(get_student_ids),notify_text)



#ap:Exam
#^ < ==============================[ <- Exam -> ]============================== > ^#
#^ Exam
#^ Dashboard Part (admin responsibility)
class ExamListCreateView(generics.ListCreateAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter,SearchFilter]
    filterset_fields = ['related_to', 'is_active','course' , 'course__teacher' ,'unit', 'video', 'type','created','start','end','allow_show_results_at']
    search_fields = ['title', 'description','course__name' , 'course__teacher__name', 'unit__name', 'video__name']
    ordering_fields = ['start', 'end']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status (existing logic)
        status = self.request.query_params.get("status")
        if status:
            now = timezone.now()
            if status == "soon":
                queryset = queryset.filter(start__gt=now)
            elif status == "active":
                queryset = queryset.filter(start__lte=now, end__gte=now)
            elif status == "finished":
                queryset = queryset.filter(end__lt=now)

        # Filter by related_course
        related_course = self.request.query_params.get("related_course")
        if related_course:
            queryset = queryset.filter(
                models.Q(unit__course_id=related_course) | models.Q(video__unit__course_id=related_course)
            )

        # Filter by related_year
        related_year = self.request.query_params.get("related_year")
        if related_year:
            queryset = queryset.filter(
                models.Q(unit__course__year_id=related_year) | models.Q(video__unit__course__year_id=related_year)
            )

        return queryset

    def perform_create(self, serializer):
        """
        Validate and save the exam, ensuring model-level validation is triggered.
        """
        if serializer.is_valid():
            try:
                exam = serializer.save()
                exam.clean()  # Trigger model validation
            except ValidationError as e:
                return Response({"errors": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExamDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

#^ QuestionCategory 
class QuestionCategoryListCreateView(generics.ListCreateAPIView):
    queryset = QuestionCategory.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = QuestionCategorySerializer
    filterset_fields = ['course']


class QuestionCategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = QuestionCategory.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = QuestionCategorySerializer

#^ Question , Answer
class QuestionListCreateView(generics.ListCreateAPIView):
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = QuestionSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = {
        'course': ['exact'],
        'video': ['exact'],
        'is_active': ['exact'],
        'category__course': ['exact'],
        'difficulty': ['exact'],
        'category': ['exact'],
        'unit__course': ['exact'],
        'question_type': ['exact'],
    }
    search_fields = ['text', 'answers__text']

    def create(self, request, *args, **kwargs):
        try:
            # Extract basic question data
            question_data = {
                'text': request.data.get('text'),
                'points': request.data.get('points'),
                'difficulty': request.data.get('difficulty'),
                'category': request.data.get('category'),
                'video': request.data.get('video'),
                'unit': request.data.get('unit'),
                # 'is_active': request.data.get('is_active') == 'true',
                'question_type': request.data.get('question_type'),
                'comment': request.data.get('comment'),
            }

            # Handle question image
            if 'image' in request.FILES:
                question_data['image'] = request.FILES.get('image')

            # Create question
            question_serializer = self.get_serializer(data=question_data)
            question_serializer.is_valid(raise_exception=True)
            question = question_serializer.save()

            # Process answers
            index = 0
            while f'answers[{index}][text]' in request.data:
                answer_data = {
                    'question': question.id,
                    'text': request.data[f'answers[{index}][text]'],
                    'is_correct': request.data.get(f'answers[{index}][is_correct]', '').lower() == 'true',
                }
                
                # Handle answer image
                image_key = f'answers[{index}][image]'
                if image_key in request.FILES:
                    answer_data['image'] = request.FILES[image_key]
                
                answer_serializer = AnswerSerializer(data=answer_data)
                if answer_serializer.is_valid():
                    answer_serializer.save()
                else:
                    # If answer creation fails, delete the question and return error
                    question.delete()
                    return Response(
                        answer_serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                index += 1

            # Return the created question with its answers
            return Response(
                self.get_serializer(question).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class QuestionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # Extract basic question data
            question_data = {}
            for field in ['text', 'points', 'difficulty', 'category', 'video', 'unit', 'question_type', 'comment']:
                if field in request.data and request.data[field]:
                    question_data[field] = request.data[field]
            
            if 'is_active' in request.data:
                question_data['is_active'] = request.data['is_active'] == 'true'

            # Handle question image
            if 'image' in request.FILES:
                question_data['image'] = request.FILES.get('image')
            elif 'image' in request.data and not request.data['image']:
                pass

            # Update question
            question_serializer = self.get_serializer(instance, data=question_data, partial=True)
            question_serializer.is_valid(raise_exception=True)
            question = question_serializer.save()

            # Get existing answers
            existing_answers = {answer.id: answer for answer in question.answers.all()}

            # Process answers
            index = 0
            while f'answers[{index}][text]' in request.data:
                answer_text = request.data.get(f'answers[{index}][text]')
                answer_id = int(request.data.get(f'answers[{index}][id]'))
                
                if answer_id in existing_answers:
                    # Update existing answer
                    answer = existing_answers[answer_id]
                    answer_data = {
                        'text': answer_text,
                        'is_correct': request.data.get(f'answers[{index}][is_correct]', '').lower() == 'true',
                        'question': question.id
                    }

                    # Handle answer image if provided
                    image_key = f'answers[{index}][image]'
                    if image_key in request.FILES:
                        answer_data['image'] = request.FILES[image_key]

                    answer_serializer = AnswerSerializer(answer, data=answer_data, partial=True)
                    if answer_serializer.is_valid():
                        answer_serializer.save()
                    else:
                        return Response(
                            answer_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                index += 1

            return Response(self.get_serializer(question).data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BulkQuestionCreateView(generics.CreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    parser_classes = (MultiPartParser, FormParser)

    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

    def create(self, request, *args, **kwargs):
        try:
            created_questions = []
            exam = None
            
            # Check if exam_id is provided and valid
            exam_id = request.data.get('exam_id')
            if exam_id:
                try:
                    exam = Exam.objects.get(id=exam_id)
                except Exam.DoesNotExist:
                    return Response(
                        {'error': 'Exam not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            with transaction.atomic():  # Use transaction to ensure all or nothing
                # Determine how many questions we're creating
                question_count = 0
                while f'questions[{question_count}][text]' in request.data:
                    question_count += 1

                # Process each question
                for q_index in range(question_count):
                    # Extract question data
                    question_data = {
                        'text': request.data.get(f'questions[{q_index}][text]'),
                        'points': request.data.get(f'questions[{q_index}][points]'),
                        'difficulty': request.data.get(f'questions[{q_index}][difficulty]'),
                        'category': request.data.get(f'questions[{q_index}][category]'),
                        'course': request.data.get(f'questions[{q_index}][course]'),
                        'video': request.data.get(f'questions[{q_index}][video]'),
                        'unit': request.data.get(f'questions[{q_index}][unit]'),
                        # 'is_active': request.data.get(f'questions[{q_index}][is_active]') == 'true',
                        'question_type': request.data.get(f'questions[{q_index}][question_type]'),
                        'comment': request.data.get(f'questions[{q_index}][comment]'),
                    }

                    # Handle question image
                    image_key = f'questions[{q_index}][image]'
                    if image_key in request.FILES:
                        question_data['image'] = request.FILES[image_key]

                    # Create question
                    question_serializer = self.get_serializer(data=question_data)
                    question_serializer.is_valid(raise_exception=True)
                    question = question_serializer.save()

                    # If exam exists, link the question to it
                    if exam:
                        ExamQuestion.objects.create(
                            exam=exam,
                            question=question,
                            is_active=True
                        )

                    # Process answers for this question
                    answer_index = 0
                    while f'questions[{q_index}][answers][{answer_index}][text]' in request.data:
                        answer_data = {
                            'question': question.id,
                            'text': request.data[f'questions[{q_index}][answers][{answer_index}][text]'],
                            'is_correct': request.data.get(f'questions[{q_index}][answers][{answer_index}][is_correct]', '').lower() == 'true',
                        }

                        # Handle answer image
                        answer_image_key = f'questions[{q_index}][answers][{answer_index}][image]'
                        if answer_image_key in request.FILES:
                            answer_data['image'] = request.FILES[answer_image_key]

                        answer_serializer = AnswerSerializer(data=answer_data)
                        answer_serializer.is_valid(raise_exception=True)
                        answer_serializer.save()
                        answer_index += 1

                    created_questions.append(question)

                # Prepare response data
                response_data = self.get_serializer(created_questions, many=True).data
                if exam:
                    response_data = {
                        'exam_id': exam.id,
                        'questions': response_data
                    }

                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


#^ Answer
class AnswerListCreateView(generics.ListCreateAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question']


class AnswerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

#^ Essay Submission
class EssaySubmissionListView(generics.ListAPIView):
    queryset = EssaySubmission.objects.all()
    permission_classes = [IsAdminUser, CustomDjangoModelPermissions]
    serializer_class = EssaySubmissionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['exam', 'student', 'student__user', 'question','result_trial','is_scored']
    search_fields = ['student__name', 'exam__title']

class ScoreEssayQuestion(APIView):
    permission_classes = [IsAdminUser, CustomDjangoModelPermissions]
    queryset = Question.objects.all()
    
    def post(self, request, submission_id):
        # Fetch the essay submission
        essay_submission = get_object_or_404(EssaySubmission, pk=submission_id)

        # Validate and get the score from JSON request body
        try:
            score = float(request.data.get("score"))
            if score is None:
                return Response(
                    {"error": "Score is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate the score
            if score > essay_submission.question.points:
                return Response(
                    {
                        "error": f"Score must be less than or equal to {essay_submission.question.points}",
                        "max_points": essay_submission.question.points
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if score < 0:
                return Response(
                    {"error": "Score cannot be negative"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid score format. Must be a number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the essay submission
        essay_submission.score = score
        essay_submission.is_scored = True
        essay_submission.save()

        # Update the result and trial scores
        result = get_object_or_404(Result, student=essay_submission.student, exam=essay_submission.exam)
        trial = essay_submission.result_trial
        
        if trial:
            # Calculate scores
            mcq_score = Submission.objects.filter(
                result_trial=trial,
                is_correct=True
            ).aggregate(total=Sum('question__points'))['total'] or 0

            essay_score = EssaySubmission.objects.filter(
                result_trial=trial,
                is_scored=True
            ).aggregate(total=Sum('score'))['total'] or 0

            total_score = mcq_score + essay_score

            # Update scores
            trial.score = total_score
            trial.save()
            
            result.score = total_score
            result.save()

        # Response data
        response_data = {
            "message": "Essay question scored successfully",
            "submission": {
                "id": essay_submission.id,
                "student_id": essay_submission.student.id,
                "exam_id": essay_submission.exam.id,
                "question_id": essay_submission.question.id,
                "score": essay_submission.score,
                "max_score": essay_submission.question.points,
                "is_scored": essay_submission.is_scored
            },
            "updated_scores": {
                "trial_score": trial.score if trial else None,
                "result_score": result.score
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)



#^ Available Questions counts and statistics with different types and filters 
class QuestionCountView(APIView):
    """
    Endpoint to get the count of questions with details.
    Allows filtering by is_active, difficulty, category, video, unit, course, and question_type.
    """
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Question.objects.all()

    def get(self, request, *args, **kwargs):
        # Build filters dynamically
        filters = Q()

        # Extract filter parameters from the query
        is_active = request.query_params.get('is_active')
        category_id = request.query_params.get('category')
        video_id = request.query_params.get('video')
        unit_id = request.query_params.get('unit')
        course_id = request.query_params.get('course')
        question_type = request.query_params.get('question_type')

        # Apply filters if provided
        if is_active is not None:  # Explicit check for None as is_active is a boolean
            filters &= Q(is_active=(is_active.lower() == 'true'))

        if category_id:
            filters &= Q(category_id=category_id)

        if video_id:
            filters &= Q(video_id=video_id)

        if unit_id:
            filters &= Q(video__unit_id=unit_id)

        if course_id:
            filters &= Q(category__course_id=course_id)

        if question_type:
            filters &= Q(question_type=question_type)

        # Aggregate counts by difficulty and question type
        total_count = Question.objects.filter(filters).count()
        active_count = Question.objects.filter(filters & Q(is_active=True)).count()
        mcq_count = Question.objects.filter(filters & Q(question_type=QuestionType.MCQ)).count()
        essay_count = Question.objects.filter(filters & Q(question_type=QuestionType.ESSAY)).count()
        easy_count = Question.objects.filter(filters & Q(difficulty=DifficultyLevel.EASY)).count()
        medium_count = Question.objects.filter(filters & Q(difficulty=DifficultyLevel.MEDIUM)).count()
        hard_count = Question.objects.filter(filters & Q(difficulty=DifficultyLevel.HARD)).count()

        # Prepare response data
        response_data = {
            "count": total_count,
            "active_count": active_count,
            "mcq_count": mcq_count,
            "essay_count": essay_count,
            "easy_count": easy_count,
            "medium_count": medium_count,
            "hard_count": hard_count,
        }

        return Response(response_data, status=status.HTTP_200_OK)


#^ Exam Questions
class GetExamQuestions(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Exam.objects.all()

    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)

        if exam.type == ExamType.RANDOM:
            return Response(
                {"message": "Random exam, I'll pick its questions randomly."},
                status=status.HTTP_200_OK
            )

        exam_questions = ExamQuestion.objects.filter(exam=exam).select_related('question')
        serializer = ExamQuestionSerializer(exam_questions, many=True)

        return Response(
            {
                "exam_id": exam.id,
                "exam_title": exam.title,
                "questions": serializer.data
            },
            status=status.HTTP_200_OK
        )



#^ add questions to an exam (manual and bank)
class AddBankExamQuestionsView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    parser_classes = [JSONParser]  # Use JSONParser to parse JSON data
    queryset = Question.objects.all()

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # Get the question IDs from the request
        question_ids = request.data.get("questions_ids", [])
        
        # Validate that question_ids is a list
        if not isinstance(question_ids, list):
            return Response(
                {"error": "Invalid format for question IDs. Expected a list of integers."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate the question IDs
        questions = Question.objects.filter(id__in=question_ids)
        invalid_ids = set(question_ids) - set(questions.values_list('id', flat=True))
        
        if invalid_ids:
            return Response(
                {"error": f"The following question IDs are invalid: {list(invalid_ids)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add the questions to the exam
        added_questions = []
        skipped_questions = []
        
        for question in questions:
            # Use get_or_create to skip existing questions
            _, created = ExamQuestion.objects.get_or_create(exam=exam, question=question)
            if created:
                added_questions.append(question.id)
            else:
                skipped_questions.append(question.id)
        
        return Response(
            {
                "message": "Questions added to the exam successfully",
                "exam_id": exam.id,
                "exam_title": exam.title,
                "added_questions": added_questions,
                "skipped_questions": skipped_questions
            },
            status=status.HTTP_201_CREATED
        )


class AddManualExamQuestionsView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    parser_classes = [MultiPartParser, FormParser]
    queryset = Question.objects.all()
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # if exam.type != ExamType.MANUAL:
        #     return Response(
        #         {"error": "This endpoint is only for manual-type exams"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        # Extract question data
        question_data = request.data.dict()
        question_data['image'] = request.FILES.get('image', None)

        # Extract and structure answers
        answers = []
        index = 0
        while f'answers[{index}][text]' in request.data:
            answer = {
                'text': request.data[f'answers[{index}][text]'],
                'is_correct': request.data.get(f'answers[{index}][is_correct]', '').lower() == 'true',
            }
            if f'answers[{index}][image]' in request.FILES:
                answer['image'] = request.FILES[f'answers[{index}][image]']
            answers.append(answer)
            index += 1

        question_data['answers'] = answers

        # Use the QuestionSerializer to validate and create the question
        serializer = QuestionSerializer(data=question_data, context={'request': request})
        if serializer.is_valid():
            question = serializer.save()
            ExamQuestion.objects.create(exam=exam, question=question)
            return Response(
                {"message": "Questions successfully created and added to the exam"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveExamQuestion(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Question.objects.all()
    def delete(self, request, exam_id, question_id):
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Fetch the exam question
        exam_question = get_object_or_404(
            ExamQuestion,
            exam=exam,
            question_id=question_id,
            is_active=True
        )

        # Remove the question from the exam (mark it as inactive)
        exam_question.delete()

        return Response(
            {"success": "Question removed from exam"},
            status=status.HTTP_200_OK
        )


#^ add questions to RandomExamBank (the small bank of questions selected for a random exam to create the models of them)
class GetRandomExamBank(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def get(self, request, exam_id):
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Validate exam type
        if exam.type != ExamType.RANDOM:
            return Response(
                {"error": "This endpoint is only for random type exams"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the random exam bank
        random_exam_bank = get_object_or_404(RandomExamBank, exam=exam)
        serializer = RandomExamBankSerializer(random_exam_bank)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AddToRandomExamBank(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def post(self, request, exam_id):
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Validate exam type
        if exam.type != ExamType.RANDOM:
            return Response(
                {"error": "This endpoint is only for random type exams"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract and validate question IDs
        question_ids = request.data.get("question_ids", [])
        questions = Question.objects.filter(id__in=question_ids)

        if len(questions) != len(question_ids):
            return Response(
                {"error": "Some question IDs are invalid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add questions to the random exam bank
        random_exam_bank, created = RandomExamBank.objects.get_or_create(exam=exam)
        random_exam_bank.questions.add(*questions)

        return Response(
            {"message": "Questions successfully added to the random exam bank"},
            status=status.HTTP_201_CREATED
        )

#^ ExamModels
class ExamModelListCreateView(generics.ListCreateAPIView):
    queryset = ExamModel.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ExamModelSerializer
    filterset_fields = ['is_active', 'exam']


class ExamModelRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExamModel.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ExamModelSerializer

#^ get examModel questions (he already added questions , to be reviewed by admin )
class GetExamModelQuestions(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def get(self, request, exam_model_id):
        # Fetch the exam model
        exam_model = get_object_or_404(ExamModel, pk=exam_model_id)

        # Fetch active questions for the exam model
        questions = [mq.question for mq in exam_model.model_questions.all()]

        # Serialize the questions
        serializer = QuestionSerializer(questions, many=True)

        # Return the response
        return Response(
            {
                "exam_model_id": exam_model.id,
                "exam_model_title": exam_model.title,
                "questions": serializer.data
            },
            status=status.HTTP_200_OK
        )


#^ Remove Question from an ExamModel
class RemoveQuestionFromExamModel(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def delete(self, request, exam_model_id, question_id):
        try:
            exam_model = get_object_or_404(ExamModel, pk=exam_model_id)
            question = get_object_or_404(Question, pk=question_id)
            exam_model_question = get_object_or_404(ExamModelQuestion, exam_model=exam_model, question=question)
            exam_model_question.delete()
            return Response(
                {"message": "Question successfully removed from the exam model"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#^ get : gets questions (randomly) from the RandomExamBank related to that exam so the teacher reviews them and modify or delete some (using other endpoints we already have)
class SuggestQuestionsForModel(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def get_random_questions(self, exam: Exam, related_questions: QuerySet) -> List[Question]:
        """
        Get random questions based on the exam's difficulty distribution.
        """
        if (
            exam.easy_questions_count == 0
            and exam.medium_questions_count == 0
            and exam.hard_questions_count == 0
        ):
            # If no difficulty distribution is specified, return random questions
            if related_questions.count() < exam.number_of_questions:
                raise ValidationError(
                    f"Not enough questions available for {exam.related_to.lower()} '{exam.get_related_name()}'"
                )
            return list(related_questions.order_by('?')[:exam.number_of_questions])

        questions = []
        for difficulty, count in [
            ("EASY", exam.easy_questions_count),
            ("MEDIUM", exam.medium_questions_count),
            ("HARD", exam.hard_questions_count)
        ]:
            if count > 0:
                difficulty_questions = related_questions.filter(difficulty=difficulty)

                if difficulty_questions.count() < count:
                    raise ValidationError(
                        f"Not enough {difficulty} questions in the bank related to the "
                        f"{exam.related_to.lower()} '{exam.get_related_name()}'."
                    )

                questions.extend(list(difficulty_questions.order_by('?')[:count]))

        return questions

    def get_related_questions(self, exam: Exam) -> QuerySet:
        """
        Get the related questions from the random exam bank.
        """
        random_exam_bank = RandomExamBank.objects.filter(exam=exam).first()
        if not random_exam_bank:
            raise ValidationError("No Available Random Bank for that Exam, please create one first.")
        return random_exam_bank.questions.all()

    def get(self, request, exam_id):
        try:
            # Fetch the exam
            exam = get_object_or_404(Exam, pk=exam_id)

            # Validate exam type
            if exam.type != ExamType.RANDOM:
                return Response(
                    {"error": "This endpoint is only for random type exams"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get related questions from the random exam bank
            related_questions = self.get_related_questions(exam)

            # Validate if there are enough questions
            if related_questions.count() < exam.number_of_questions:
                raise ValidationError(
                    f"Not enough questions available for {exam.related_to.lower()} '{exam.get_related_name()}'"
                )

            # Get random questions based on the exam's difficulty distribution
            random_questions = self.get_random_questions(exam, related_questions)

            # Serialize the questions
            serializer = QuestionSerializer(random_questions, many=True)

            # Return the response
            return Response({
                "exam_id": exam.id,
                "exam_title": exam.title,
                "questions": serializer.data
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# post : receives the reviewed suggestions and modified questions to store them in the ExamModelQuestion )
class AddQuestionsToModel(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def post(self, request, exam_id, exam_model_id):
        try:
            # Get the Exam and ExamModel objects
            exam = get_object_or_404(Exam, pk=exam_id)
            exam_model = get_object_or_404(ExamModel, pk=exam_model_id, exam=exam)

            # Validate exam type
            if exam.type != ExamType.RANDOM:
                return Response(
                    {"error": "This endpoint is only for random type exams"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the question IDs from the request
            question_ids = request.data.get("question_ids", [])

            # Validate the question IDs
            questions = Question.objects.filter(id__in=question_ids)
            invalid_ids = set(question_ids) - set(questions.values_list('id', flat=True))
            if invalid_ids:
                return Response(
                    {"error": f"The following question IDs are invalid: {list(invalid_ids)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Add the questions to the ExamModel
            added_questions = []
            skipped_questions = []
            for question in questions:
                # Use get_or_create to skip existing questions
                _, created = ExamModelQuestion.objects.get_or_create(exam_model=exam_model, question=question)
                if created:
                    added_questions.append(question.id)
                else:
                    skipped_questions.append(question.id)

            return Response({
                "message": "Questions added to the exam model successfully",
                "model_id": exam_model.id,
                "title": exam_model.title,
                "added_questions": added_questions,
                "skipped_questions": skipped_questions
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#^ Results
from django.db import connection

class ResultListView(generics.ListAPIView):
    serializer_class = ResultSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = {
        'student': ['exact'],
        'exam': ['exact'],
        'exam__unit': ['exact'],
        'exam__video': ['exact'],
        'exam__related_to': ['exact'],
    }
    search_fields = [
        'student__name',
        'student__user__username',
        'exam__title',
        'exam__description'
    ]

    def list(self, request, *args, **kwargs):
        """Override list method to handle custom queryset"""
        data = self.get_custom_data()
        
        # Handle pagination
        page = self.paginate_queryset(data)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
    
    def get_custom_data(self):
        # Your existing SQL query logic
        base_sql = '''
            SELECT DISTINCT
                er.id,
                er.exam_id,
                er.student_id,
                er.trial,
                er.exam_model_id,
                COALESCE(ert.score, 0) as student_score,
                COALESCE(ert.exam_score, 0) as exam_score,
                ert.student_started_exam_at,
                ert.student_submitted_exam_at,
                ert.submit_type,
                e.number_of_allowed_trials,
                e.allow_show_results_at,
                e.title as exam_title,
                e.description as exam_description,
                s.name as student_name,
                s.parent_phone,
                s.jwt_token,
                u.username as student_phone,
                COALESCE(sub_correct.count, 0) as correct_questions_count,
                COALESCE(sub_incorrect.count, 0) as incorrect_questions_count,
                COALESCE(sub_unsolved.count, 0) as unsolved_questions_count
            FROM exam_result er
            LEFT JOIN exam_resulttrial ert ON ert.result_id = er.id AND ert.trial = er.trial
            LEFT JOIN exam_exam e ON er.exam_id = e.id
            LEFT JOIN student_student s ON er.student_id = s.id
            LEFT JOIN auth_user u ON s.user_id = u.id
            LEFT JOIN (
                SELECT
                    result_trial_id,
                    COUNT(*) as count
                FROM exam_submission
                WHERE is_correct = true
                GROUP BY result_trial_id
            ) sub_correct ON sub_correct.result_trial_id = ert.id
            LEFT JOIN (
                SELECT
                    result_trial_id,
                    COUNT(*) as count
                FROM exam_submission
                WHERE is_correct = false
                GROUP BY result_trial_id
            ) sub_incorrect ON sub_incorrect.result_trial_id = ert.id
            LEFT JOIN (
                SELECT
                    result_trial_id,
                    COUNT(*) as count
                FROM exam_submission
                WHERE is_solved = false
                GROUP BY result_trial_id
            ) sub_unsolved ON sub_unsolved.result_trial_id = ert.id
        '''

        # Add filters
        where_conditions = []
        params = []

        # Handle basic filters
        student_id = self.request.query_params.get('student')
        if student_id:
            where_conditions.append('er.student_id = %s')
            params.append(student_id)

        exam_id = self.request.query_params.get('exam')
        if exam_id:
            where_conditions.append('er.exam_id = %s')
            params.append(exam_id)

        # Handle submitted filter
        submitted = self.request.query_params.get('submitted')
        if submitted:
            submitted = submitted.lower()
            if submitted in ('true', '1'):
                where_conditions.append('ert.student_submitted_exam_at IS NOT NULL')
            elif submitted in ('false', '0'):
                where_conditions.append('ert.student_submitted_exam_at IS NULL')

        # Handle score filters
        score_from = self.request.query_params.get('score_from')
        if score_from:
            try:
                score_from = float(score_from)
                where_conditions.append('COALESCE(ert.score, 0) >= %s')
                params.append(score_from)
            except (ValueError, TypeError):
                pass

        score_to = self.request.query_params.get('score_to')
        if score_to:
            try:
                score_to = float(score_to)
                where_conditions.append('COALESCE(ert.score, 0) <= %s')
                params.append(score_to)
            except (ValueError, TypeError):
                pass

        # Handle search
        search = self.request.query_params.get('search')
        if search:
            search_condition = '''(
                s.name ILIKE %s OR
                u.username ILIKE %s OR
                e.title ILIKE %s OR
                e.description ILIKE %s
            )'''
            where_conditions.append(search_condition)
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param, search_param])

        # Add WHERE clause if we have conditions
        if where_conditions:
            base_sql += ' WHERE ' + ' AND '.join(where_conditions)

        # Handle ordering
        ordering = self.request.query_params.get('ordering', '-student_score')
        if ordering == 'student_score':
            base_sql += ' ORDER BY student_score ASC'
        elif ordering == '-student_score':
            base_sql += ' ORDER BY student_score DESC'
        elif ordering == 'exam_score':
            base_sql += ' ORDER BY exam_score ASC'
        elif ordering == '-exam_score':
            base_sql += ' ORDER BY exam_score DESC'
        elif ordering == 'student__name':
            base_sql += ' ORDER BY student_name ASC'
        elif ordering == '-student__name':
            base_sql += ' ORDER BY student_name DESC'
        else:
            base_sql += ' ORDER BY student_score DESC'

        # Execute the query
        with connection.cursor() as cursor:
            cursor.execute(base_sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Convert to Result objects for compatibility
        result_objects = []
        for row in results:
            result = Result(
                id=row['id'],
                exam_id=row['exam_id'],
                student_id=row['student_id'],
                trial=row['trial']
            )
            # Add the calculated fields as attributes
            result.student_score = row['student_score']
            result.exam_score = row['exam_score']
            
            # Handle timezone-aware datetime fields
            result.student_started_exam_at = self._make_timezone_aware(row['student_started_exam_at'])
            result.student_submitted_exam_at = self._make_timezone_aware(row['student_submitted_exam_at'])
            result.allow_show_results_at = self._make_timezone_aware(row['allow_show_results_at'])
            
            result.submit_type = row['submit_type']
            result.correct_questions_count = row['correct_questions_count']
            result.incorrect_questions_count = row['incorrect_questions_count']
            result.unsolved_questions_count = row['unsolved_questions_count']
            result.student_name = row['student_name']
            result.student_phone = row['student_phone']
            result.parent_phone = row['parent_phone']
            result.jwt_token = row['jwt_token']
            result.number_of_allowed_trials = row['number_of_allowed_trials']

            result_objects.append(result)

        return result_objects

    def _make_timezone_aware(self, dt):
        """Helper method to ensure datetime is timezone-aware"""
        if dt is None:
            return None
        
        # If it's already timezone-aware, return as is
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            return dt
        
        # If it's naive, make it timezone-aware
        if hasattr(dt, 'replace'):
            # Assume it's in UTC if naive
            from datetime import timezone as dt_timezone
            return timezone.make_aware(dt, dt_timezone.utc) if dt.tzinfo is None else dt
        
        return dt

    def get_queryset(self):
        """Required by DRF but not used in our custom implementation"""
        return Result.objects.none()


class ReduceResultTrialView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Exam.objects.all()
        
    
    def post(self, request, result_id):
        result = get_object_or_404(Result, pk=result_id)
        
        if result.trial == 0:
            return Response(
                {"error": "No trials exist for this result."},
                status=status.HTTP_400_BAD_REQUEST
            )

        last_trial = result.trials.filter(trial=result.trial).first()
        if not last_trial:
            return Response(
                {"error": "No trial found for the current trial count."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Delete related submissions and essay submissions
            Submission.objects.filter(result_trial=last_trial).delete()
            EssaySubmission.objects.filter(result_trial=last_trial).delete()
            
            last_trial.delete()
            result.trial -= 1

            if result.trial == 0:
                result.delete()
                return Response(
                    {"message": "Trial reduced successfully. Result deleted as trial count reached zero."},
                    status=status.HTTP_200_OK
                )

            result.save()

        return Response(
            {"message": "Trial reduced successfully.", "new_trial_count": result.trial},
            status=status.HTTP_200_OK
        )


class ExamResultDetailView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Result.objects.all()

    def get(self, request, result_id):
        result = get_object_or_404(Result, pk=result_id)
        active_trial = result.active_trial

        # Fetch both MCQ and Essay submissions
        mcq_submissions = Submission.objects.filter(
            result_trial=active_trial
        ).select_related('question', 'selected_answer', 'question__category')

        essay_submissions = EssaySubmission.objects.filter(
            result_trial=active_trial
        ).select_related('question', 'question__category')

        # Calculate counts
        correct_mcq_count = mcq_submissions.filter(is_correct=True).count()
        incorrect_mcq_count = mcq_submissions.filter(is_correct=False, is_solved=True).count()
        unsolved_mcq_count = mcq_submissions.filter(is_solved=False).count()
        correct_essay_count = essay_submissions.filter(is_scored=True, score__gt=0).count()
        incorrect_essay_count = essay_submissions.filter(is_scored=True, score=0).count()
        unscored_essay_count = essay_submissions.filter(is_scored=False).count()

        student_answers = []
        # unsolved_questions = []  # Commented out as requested
        # unscored_essay_questions = []  # Commented out as requested

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            answer_data = self._build_mcq_answer_data(submission, question)
            student_answers.append(answer_data)
            # if not submission.is_solved:
            #     unsolved_questions.append(answer_data)  # Commented out

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = self._build_essay_answer_data(submission, question)
            student_answers.append(answer_data)
            # if not submission.is_scored:
            #     unscored_essay_questions.append(answer_data)  # Commented out

        # Fetch correct answers and questions (commented out in response, but code kept for potential future use)
        questions = Question.objects.filter(
            exam_questions__exam=result.exam
        ).select_related('category').prefetch_related('answers').distinct()

        # correct_answers = [self._build_correct_answer_data(q) for q in questions]  # Kept for potential future use

        # Fetch all trials
        trials = result.trials.all().order_by('trial')
        trial_data = [{
            "trial_number": trial.trial,
            "score": trial.score,
            "exam_score": trial.exam_score,
            "student_started_exam_at": trial.student_started_exam_at,
            "student_submitted_exam_at": trial.student_submitted_exam_at,
            "submit_type": trial.submit_type,
            "trial_id": trial.id,
        } for trial in trials]

        # Determine if the student succeeded in this trial
        is_succeeded = False
        if active_trial.exam_score and active_trial.score is not None:
            is_succeeded = active_trial.score >= (result.exam.passing_percent / 100) * active_trial.exam_score

        response_data = {
            "active_trial": active_trial.id,
            "trial_number": active_trial.trial,
            "student_id": result.student.id,
            "student_name": result.student.name,
            "exam_id": result.exam.id,
            "exam_title": result.exam.title,
            "exam_description": result.exam.description,
            "exam_score": active_trial.exam_score if active_trial else 0,
            "student_score": active_trial.score if active_trial else 0,
            "is_succeeded": is_succeeded,
            "student_trials": result.trial,
            "is_trials_finished": result.is_trials_finished,
            # Counts
            "number_of_essay": essay_submissions.count(),
            "number_of_mcq": mcq_submissions.count(),
            "correct_mcq_count": correct_mcq_count,
            "incorrect_mcq_count": incorrect_mcq_count,
            "unsolved_mcq_count": unsolved_mcq_count,
            "correct_essay_count": correct_essay_count,
            "incorrect_essay_count": incorrect_essay_count,
            "unscored_essay_count": unscored_essay_count,
            # Answer data
            "student_answers": student_answers,
            # "unsolved_questions": unsolved_questions,  # Commented out as requested
            # "unscored_essay_questions": unscored_essay_questions,  # Commented out as requested
            # "correct_answers": correct_answers,  # Commented out as requested
            "trials": trial_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _build_mcq_answer_data(self, submission, question):
        # Get all answers for this question
        answers = Answer.objects.filter(question=question)
        answer_details = [
            {
                "id": ans.id,
                "text": ans.text,
                "image": ans.image.url if ans.image else None,
                "is_correct": ans.is_correct
            }
            for ans in answers
        ]

        # Build the selected answer object
        selected_answer_obj = None
        if submission.selected_answer:
            selected_answer_obj = {
                "id": submission.selected_answer.id,
                "text": submission.selected_answer.text,
                "image": submission.selected_answer.image.url if submission.selected_answer.image else None,
                "is_correct": submission.selected_answer.is_correct
            }

        # Build the full answer data object
        return {
            "submission_id": submission.id,
            "type": "mcq",
            "question_id": question.id,
            "question_category": question.category.title if question.category else None,
            "question_category_id": question.category.id if question.category else None,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "question_comment": question.comment,
            "selected_answer": selected_answer_obj,
            "is_correct": submission.is_correct,
            "is_solved": submission.is_solved,
            "points": question.points,
            "answers": answer_details
        }

    def _build_essay_answer_data(self, submission, question):
        return {
            "submission_id": submission.id,
            "type": "essay",
            "question_id": question.id,
            "question_category": question.category.title if question.category else None,
            "question_category_id": question.category.id if question.category else None,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "question_comment": question.comment,
            "answer_text": submission.answer_text,
            "answer_file": submission.answer_file.url if submission.answer_file else None,
            "score": submission.score,
            "is_scored": submission.is_scored,
            "points": question.points,
            "answers": []  # Essays don't have predefined answers like MCQ
        }

    def _build_correct_answer_data(self, question):
        return {
            "question_id": question.id,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "question_comment": question.comment,
            "category_title": question.category.title if question.category else None,
            "category_id": question.category.id if question.category else None,
            "correct_answers": [
                {
                    "text": answer.text,
                    "image": answer.image.url if answer.image else None,
                    "is_correct": answer.is_correct
                }
                for answer in question.answers.all()
            ],
            "question_type": question.question_type,
        }


class ExamResultDetailForTrialView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Result.objects.all()

    def get(self, request, result_id, result_trial_id):
        # Fetch the result
        result = get_object_or_404(Result, pk=result_id)

        # Fetch the specific trial and ensure it belongs to the result
        trial = get_object_or_404(ResultTrial, pk=result_trial_id, result=result)

        # Fetch both MCQ and Essay submissions for this trial
        mcq_submissions = Submission.objects.filter(
            result_trial=trial
        ).select_related('question', 'selected_answer', 'question__category')

        essay_submissions = EssaySubmission.objects.filter(
            result_trial=trial
        ).select_related('question', 'question__category')

        # Calculate counts
        correct_mcq_count = mcq_submissions.filter(is_correct=True).count()
        incorrect_mcq_count = mcq_submissions.filter(is_correct=False, is_solved=True).count()
        unsolved_mcq_count = mcq_submissions.filter(is_solved=False).count()
        correct_essay_count = essay_submissions.filter(is_scored=True, score__gt=0).count()
        incorrect_essay_count = essay_submissions.filter(is_scored=True, score=0).count()
        unscored_essay_count = essay_submissions.filter(is_scored=False).count()

        student_answers = []
        # unsolved_questions = []  # Commented out as requested
        # unscored_essay_questions = []  # Commented out as requested

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            answer_data = self._build_mcq_answer_data(submission, question)
            student_answers.append(answer_data)
            # if not submission.is_solved:
            #     unsolved_questions.append(answer_data)  # Commented out

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = self._build_essay_answer_data(submission, question)
            student_answers.append(answer_data)
            # if not submission.is_scored:
            #     unscored_essay_questions.append(answer_data)  # Commented out

        # Fetch correct answers and questions (commented out in response, but code kept for potential future use)
        questions = Question.objects.filter(
            exam_questions__exam=result.exam
        ).select_related('category').prefetch_related('answers').distinct()

        # correct_answers = [self._build_correct_answer_data(q) for q in questions]  # Kept for potential future use

        # Fetch all trials for this result (including the current one)
        trials = result.trials.all().order_by('trial')
        trial_data = [{
            "trial_number": t.trial,
            "score": t.score,
            "exam_score": t.exam_score,
            "student_started_exam_at": t.student_started_exam_at,
            "student_submitted_exam_at": t.student_submitted_exam_at,
            "submit_type": t.submit_type,
            "trial_id": t.id,
            "is_active": t.id == trial.id  # Mark the current trial as active in the list
        } for t in trials]

        # Determine if the student succeeded in this trial
        is_succeeded = False
        if trial.exam_score and trial.score is not None:
            is_succeeded = trial.score >= (result.exam.passing_percent / 100) * trial.exam_score

        response_data = {
            "active_trial": trial.id,  # The trial we're looking at
            "trial_number": trial.trial,
            "student_id": result.student.id,
            "student_name": result.student.name,
            "exam_id": result.exam.id,
            "exam_title": result.exam.title,
            "exam_description": result.exam.description,
            "exam_score": trial.exam_score if trial else 0,
            "student_score": trial.score if trial else 0,
            "is_succeeded": is_succeeded,
            "student_trials": result.trial,
            "is_trials_finished": result.is_trials_finished,
            # Counts
            "number_of_essay": essay_submissions.count(),
            "number_of_mcq": mcq_submissions.count(),
            "correct_mcq_count": correct_mcq_count,
            "incorrect_mcq_count": incorrect_mcq_count,
            "unsolved_mcq_count": unsolved_mcq_count,
            "correct_essay_count": correct_essay_count,
            "incorrect_essay_count": incorrect_essay_count,
            "unscored_essay_count": unscored_essay_count,
            # Answer data
            "student_answers": student_answers,
            # "unsolved_questions": unsolved_questions,  # Commented out as requested
            # "unscored_essay_questions": unscored_essay_questions,  # Commented out as requested
            # "correct_answers": correct_answers,  # Commented out as requested
            "trials": trial_data,
            # Additional trial-specific info
            "selected_trial_id": trial.id,
            "student_started_exam_at": trial.student_started_exam_at,
            "student_submitted_exam_at": trial.student_submitted_exam_at,
            "submit_type": trial.submit_type,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _build_mcq_answer_data(self, submission, question):
        # Get all answers for this question
        answers = Answer.objects.filter(question=question)
        answer_details = [
            {
                "id": ans.id,
                "text": ans.text,
                "image": ans.image.url if ans.image else None,
                "is_correct": ans.is_correct
            }
            for ans in answers
        ]

        # Build the selected answer object
        selected_answer_obj = None
        if submission.selected_answer:
            selected_answer_obj = {
                "id": submission.selected_answer.id,
                "text": submission.selected_answer.text,
                "image": submission.selected_answer.image.url if submission.selected_answer.image else None,
                "is_correct": submission.selected_answer.is_correct
            }

        # Build the full answer data object
        return {
            "submission_id": submission.id,
            "type": "mcq",
            "question_id": question.id,
            "question_category": question.category.title if question.category else None,
            "question_category_id": question.category.id if question.category else None,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "question_comment": question.comment,
            "selected_answer": selected_answer_obj,
            "is_correct": submission.is_correct,
            "is_solved": submission.is_solved,
            "points": question.points,
            "answers": answer_details
        }

    def _build_essay_answer_data(self, submission, question):
        return {
            "submission_id": submission.id,
            "type": "essay",
            "question_id": question.id,
            "question_category": question.category.title if question.category else None,
            "question_category_id": question.category.id if question.category else None,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "question_comment": question.comment,
            "answer_text": submission.answer_text,
            "answer_file": submission.answer_file.url if submission.answer_file else None,
            "score": submission.score,
            "is_scored": submission.is_scored,
            "points": question.points,
            "answers": []  # Essays don't have predefined answers like MCQ
        }

    def _build_correct_answer_data(self, question):
        return {
            "question_id": question.id,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "question_comment": question.comment,
            "category_title": question.category.title if question.category else None,
            "category_id": question.category.id if question.category else None,
            "correct_answers": [
                {
                    "text": answer.text,
                    "image": answer.image.url if answer.image else None,
                    "is_correct": answer.is_correct
                }
                for answer in question.answers.all()
            ],
            "question_type": question.question_type,
        }


class ResultTrialsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ResultTrialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['submit_type']

    def get_queryset(self):
        result_id = self.kwargs['result_id']
        result = get_object_or_404(Result, id=result_id)
        return result.trials.all().annotate(
            mcq_score=Sum('submissions__question__points', filter=models.Q(submissions__is_correct=True)),
            essay_score=Sum('essay_submissions__score', filter=models.Q(essay_submissions__is_scored=True))
        ).order_by('trial')


#^ get students who toke the exam and those who didn't
class StudentsTookExamAPIView(generics.ListAPIView):
    serializer_class = FlattenedStudentResultSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    
    def get_queryset(self):
        exam_id = self.kwargs['exam_id']
        exam = get_object_or_404(Exam, id=exam_id)

        # Get the related course for the exam
        related_course_id = exam.get_related_course()
        if not related_course_id:
            return Response({"error": "Exam is not related to any course"}, status=status.HTTP_400_BAD_REQUEST)

        # Get students who are subscribed to the related course
        # subscribed_students = Student.objects.all()
        subscribed_students = Student.objects.filter(
            coursesubscription__course_id=related_course_id,
            coursesubscription__active=True
        ).distinct()

        # Filter by student.is_center if the query parameter is provided
        is_center_filter = self.request.query_params.get('is_center', None)
        if is_center_filter is not None:
            is_center_filter = is_center_filter.lower() == 'true'  # Convert to boolean
            subscribed_students = subscribed_students.filter(is_center=is_center_filter)

        # Get students who took the exam (from the subscribed students)
        students_took_exam = subscribed_students.filter(result__exam=exam).distinct()

        # Search functionality
        search_query = self.request.query_params.get('search', None)
        if search_query:
            students_took_exam = students_took_exam.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(parent_phone__icontains=search_query) |
                Q(government__icontains=search_query)
            )

        # Prefetch related Result and ResultTrial data
        students_took_exam = students_took_exam.prefetch_related(
            Prefetch('result_set', queryset=Result.objects.filter(exam=exam).prefetch_related('trials'))
        )

        return students_took_exam
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['exam_id'] = self.kwargs['exam_id']
        return context


class StudentsDidNotTakeExamAPIView(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    

    def get_queryset(self):
        exam_id = self.kwargs['exam_id']
        exam = get_object_or_404(Exam, id=exam_id)

        # Get the related course for the exam
        related_course_id = exam.get_related_course()
        if not related_course_id:
            return Response({"error": "Exam is not related to any course"}, status=status.HTTP_400_BAD_REQUEST)

        # Get students who are subscribed to the related course
        subscribed_students = Student.objects.filter(
            coursesubscription__course_id=related_course_id,
            coursesubscription__active=True
        ).distinct()

        # Filter by student.is_center if the query parameter is provided
        is_center_filter = self.request.query_params.get('is_center', None)
        if is_center_filter is not None:
            is_center_filter = is_center_filter.lower() == 'true'  # Convert to boolean
            subscribed_students = subscribed_students.filter(is_center=is_center_filter)

        # Get students who didn't take the exam (from the subscribed students)
        students_did_not_take_exam = subscribed_students.exclude(result__exam=exam).distinct()

        # Search functionality
        search_query = self.request.query_params.get('search', None)
        if search_query:
            students_did_not_take_exam = students_did_not_take_exam.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(parent_phone__icontains=search_query) |
                Q(government__icontains=search_query)
            )

        return students_did_not_take_exam


class ExamsTakenByStudentAPIView(generics.ListAPIView):
    serializer_class = FlattenedExamResultSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    
    def get_queryset(self):
        student_id = self.kwargs['student_id']
        student = get_object_or_404(Student, id=student_id)

        # Get exams taken by the student
        exams_taken = Exam.objects.filter(results__student=student).distinct()

        # Search functionality
        search_query = self.request.query_params.get('search', None)
        if search_query:
            exams_taken = exams_taken.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        # Optimize the query with select/prefetch_related
        exams_taken = exams_taken.select_related(
            'unit', 'video'
        ).prefetch_related(
            'unit__course__year', 
            'video__unit__course__year',
            Prefetch(
                'results',
                queryset=Result.objects.filter(student=student).prefetch_related('trials'),
                to_attr='student_results'
            )
        )

        return exams_taken
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['student_id'] = self.kwargs['student_id']
        return context


class ExamsNotTakenByStudentAPIView(generics.ListAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

    def get_queryset(self):
        student_id = self.kwargs['student_id']
        student = get_object_or_404(Student, id=student_id)
        
        # Get active course subscriptions for the student
        student_course_subscriptions = CourseSubscription.objects.filter(
            student=student, 
            active=True
        )
        
        # Get the IDs of subscribed courses
        subscribed_course_ids = student_course_subscriptions.values_list('course_id', flat=True)
        
        # Get exams from subscribed courses only
        subscribed_exams = Exam.objects.filter(
            Q(unit__course_id__in=subscribed_course_ids) | 
            Q(video__unit__course_id__in=subscribed_course_ids)
        ).distinct()
        
        # Get exams taken by the student
        exams_taken = Exam.objects.filter(results__student=student).distinct()
        
        # Get exams not taken by the student (from subscribed courses only)
        exams_not_taken = subscribed_exams.exclude(id__in=exams_taken.values('id'))
        
        # Search functionality (optional, if needed)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            exams_not_taken = exams_not_taken.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        return exams_not_taken


class CopyExamView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, exam_id):
        serializer = CopyExamSerializer(data=request.data)
        if serializer.is_valid():
            original_exam = Exam.objects.get(pk=exam_id)
            data = serializer.validated_data

            # Create a copy
            new_exam = Exam.objects.create(
                title=original_exam.title,
                description=original_exam.description,
                related_to=data['related_to'],
                unit=data.get('unit'),
                video=data.get('video'),
                course=data['course'],
                number_of_questions=original_exam.number_of_questions,
                time_limit=original_exam.time_limit,
                score=original_exam.score,
                passing_percent=original_exam.passing_percent,
                start=original_exam.start,
                end=original_exam.end,
                number_of_allowed_trials=original_exam.number_of_allowed_trials,
                type=original_exam.type,
                easy_questions_count=original_exam.easy_questions_count,
                medium_questions_count=original_exam.medium_questions_count,
                hard_questions_count=original_exam.hard_questions_count,
                show_answers_after_finish=original_exam.show_answers_after_finish,
                order=original_exam.order,
                is_active=original_exam.is_active,
                allow_show_results_at=original_exam.allow_show_results_at,
                allow_show_answers_at=original_exam.allow_show_answers_at,
                is_depends=original_exam.is_depends,
            )

            # Copy exam questions
            for eq in original_exam.exam_questions.all():
                ExamQuestion.objects.create(
                    exam=new_exam,
                    question=eq.question,
                    is_active=eq.is_active
                )

            return Response({"id": new_exam.id, "message": "Exam copied successfully."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExamQuestionReorderAPIView(APIView):
    """
    APIView to reorder ExamQuestion instances.
    Expects a list of dictionaries, each containing 'exam_question' (ID)
    and 'new_order'.
    """
    def post(self, request, *args, **kwargs):
        serializer = ExamQuestionReorderSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    for item in serializer.validated_data:
                        exam_question_id = item['exam_question']
                        new_order = item['new_order']

                        try:
                            exam_question = ExamQuestion.objects.get(id=exam_question_id)
                            exam_question.order = new_order
                            exam_question.save()
                        except ExamQuestion.DoesNotExist:
                            # This case should ideally be caught by the serializer's validation,
                            # but it's good to have a fallback.
                            return Response(
                                {"detail": f"ExamQuestion with ID {exam_question_id} not found."},
                                status=status.HTTP_404_NOT_FOUND
                            )
                return Response({"detail": "ExamQuestions reordered successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"detail": f"An error occurred during reordering: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#^ < ==============================[ <- Student Temp Exams -> ]============================== > ^#

class CreateOrUpdateTempExamAllowedTimes(APIView):
    permission_classes = [IsAdminUser]
    QuerySet = TempExamAllowedTimes.objects.all()

    def post(self, request):
        serializer = TempExamAllowedTimesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create or update the single instance
        instance, created = TempExamAllowedTimes.objects.get_or_create(
            id=1,
            defaults=serializer.validated_data
        )

        if not created:
            # Update existing instance
            for attr, value in serializer.validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        return Response({
            "message": "Temp exam allowed times updated successfully",
            "number_of_allowedtempexams_per_day": instance.number_of_allowedtempexams_per_day
        }, status=status.HTTP_200_OK)

#^ < ==============================[ <- video quiz -> ]============================== > ^#

class VideoQuizListCreateAPIView(generics.ListCreateAPIView):
    queryset = VideoQuiz.objects.all()
    serializer_class = VideoQuizSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    filterset_fields = [
            'exam',
            'course',
            'video',
            ]

    search_fields = [
        'exam__title',
            'course__name',
            'course__description',
            'video__name',
            'video__description',
            
        ]


class VideoQuizRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VideoQuiz.objects.all()
    serializer_class = VideoQuizSerializer


