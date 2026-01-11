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
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
# FILES
from core.permissions import IsTeacher
from exam.serializers import ExamSerializer
from exam.models import Exam
from subscription.models import CourseSubscription
from view.models import VideoView,ViewSession
from dashboard.filters import ViewSessionFilter
from .models import *
from .serializers.profile.profile import *
from .serializers.course.course import *
from .serializers.student.student import*
from .serializers.subscription.subscription import *
from .serializers.invoice.Invoice import *
from .serializers.view.view import ListVideoViewListSerializer,ViewSessionListSerializer

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
    permission_classes = [IsAuthenticated]
    def get(self,request,*args, ** kwargs):
        qr = TeacherCourseCategory.objects.filter(teacher=request.user.teacher).values("course_category__id",'course_category__name')
        return Response(qr,status=status.HTTP_200_OK)


#* < ==============================[ <- Course -> ]============================== > ^#

#* Course
#list
class TeacherListCourseView(generics.ListAPIView):
    serializer_class = TeacherListCourseSerializer
    permission_classes = [IsAuthenticated,IsTeacher]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = [
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
    
    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user.teacher)

#simple list
class TeacherListCourseSimpleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        year_id = request.query_params.get('year_id')
        qr = Course.objects.filter(teacher=self.request.user.teacher).values("id", "name",'price')

        if year_id:
            qr = qr.filter(year_id=year_id)

        return Response(qr, status=status.HTTP_200_OK)

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

#simple list
class TeacherUnitListSimple(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,course_id,*args, ** kwargs):
        qr = Unit.objects.filter(course_id=course_id,course__teacher=request.user.teacher).values("id",'name')
        return Response(qr,status=status.HTTP_200_OK)

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


class TeacherAllVideos(generics.ListAPIView):
    serializer_class = TeacherListVideoSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    def get_queryset(self):
        return Video.objects.filter(unit__course__teacher=self.request.user.teacher)

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


#video files
#list
class TeacherVideoFileListView(generics.ListAPIView):
    serializer_class = TeacherFileVideoSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        video_id = self.kwargs['video_id']
        video = get_object_or_404(Video, id=video_id, unit__course__teacher=self.request.user.teacher)
        return video.video_files.all()


#create
class TeacherVideoFileCreateView(generics.CreateAPIView):
    serializer_class = TeacherFileVideoSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def perform_create(self, serializer):
        video_id = self.kwargs['video_id']
        video = get_object_or_404(Video, id=video_id, unit__course__teacher=self.request.user.teacher)
        serializer.save(video=video)

#delete
class TeacherVideoFileDeleteView(generics.DestroyAPIView):
    serializer_class = TeacherFileVideoSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_field = 'file_id'
    
    def get_object(self):
        video_file = get_object_or_404(VideoFile, id=self.kwargs['file_id'], video__unit__course__teacher=self.request.user.teacher)
        return video_file



#* File 

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
    

#* < ==============================[ <- Invoice -> ]============================== > ^#

class TeacherInvoiceList(generics.ListAPIView):
    serializer_class = ListInvoiceSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    filter_backends = [DjangoFilterBackend, SearchFilter]

    search_fields = [
        'student__name',
        'student__user__username',
        'course__name',
        'invoice__sequence',
    ]

    def get_queryset(self):
        return Invoice.objects.filter(teacher=self.request.user.teacher)


#* < ==============================[ <- Subscription -> ]============================== > ^#

class TeacherCourseSubscriptionList(generics.ListAPIView):
    serializer_class = TeacherListStudentCourseSubscription
    permission_classes = [IsAuthenticated, IsTeacher]
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
            'course',
            'active',
            'student__government'
        ]
    
    def get_queryset(self):
        return CourseSubscription.objects.filter(course__teacher=self.request.user.teacher)


class TeacherCancelSubscription(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request, *args, **kwargs):
        subscription_id = request.data.get('subscription_id')
        subscription = get_object_or_404(CourseSubscription, id=subscription_id, course__teacher=request.user.teacher)

        if not subscription.active:
            raise PermissionDenied("This subscription is already inactive.")

        # Cancel the subscription
        subscription.active = False
        subscription.save()

        return Response({"message": "Subscription cancelled successfully."}, status=status.HTTP_200_OK)



class TeacherRenewSubscription(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request, *args, **kwargs):
        subscription_id = request.data.get('subscription_id')
        subscription = get_object_or_404(CourseSubscription, id=subscription_id, course__teacher=request.user.teacher)

        if subscription.active:
            raise PermissionDenied("This subscription is already active.")

        # Renew the subscription
        subscription.active = True
        subscription.save()

        return Response({"message": "Subscription renewed successfully."}, status=status.HTTP_200_OK)



#* < ==============================[ <- Student -> ]============================== > ^#

class TeacherListStudentView(generics.ListAPIView):
    serializer_class = TeacherStudentSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return Student.objects.filter(
            coursesubscription__course__teacher=self.request.user.teacher
        ).distinct()
        

class TeacherStudentDetailView(generics.RetrieveAPIView):
    serializer_class = TeacherStudentSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_url_kwarg = "student_id"

    def get_queryset(self):
        # Students linked to teacher via course subscriptions
        return Student.objects.filter(
            coursesubscription__course__teacher=self.request.user.teacher
        ).distinct()


class TeacherCenterStudentSignUpView(APIView):
    permission_classes = [IsAuthenticated,IsTeacher]

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        get_code = get_object_or_404(TeacherCenterStudentCode, code=code, is_available=True)
        get_code.student = request.user.student
        get_code.is_available = False
        get_code.save()
        return Response(status=status.HTTP_200_OK)




class TeacherStudentLoginSessionView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    serializer_class = TeacherStudentLoginSessionSerializer
    filterset_fields = [
            'student_id',
        ]
        
    def get_queryset(self):
        return StudentLoginSession.objects.filter(
            student__coursesubscription__course__teacher=self.request.user.teacher
        ).select_related('student').distinct()


#* < ==============================[ <- Views -> ]============================== > ^#

class TeacherVideoViewList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
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
    
    
    def get_queryset(self):
        return VideoView.objects.filter(video__unit__course__teacher=self.request.user.teacher)

class TeacherVideoViewSessionsList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ViewSessionListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'session',
        'view__student__user__username',
    ]
    filterset_class = ViewSessionFilter 
    
    def get_queryset(self):
        return ViewSession.objects.filter(view__video__unit__course__teacher=self.request.user.teacher)

#ap:Exam
#^ < ==============================[ <- Exam -> ]============================== > ^#
#^ Exam

from django.shortcuts import get_object_or_404
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Sum, F, Case, BooleanField, Prefetch
from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from exam.models import (
    Answer, DifficultyLevel, Exam, ExamModel, ExamModelQuestion, ExamQuestion, 
    ExamType, Question, QuestionCategory, QuestionType, RandomExamBank, 
    RelatedToChoices, Result, EssaySubmission, ResultTrial, Submission, 
    TempExamAllowedTimes, VideoQuiz
)
from .serializers.exam.exam import *
from django.db.models import When


class TeacherPermissionMixin:
    """Mixin to check if user is a teacher and filter by teacher's courses"""
    
    def get_teacher(self):
        """Get the teacher instance for the current user"""
        try:
            return Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return None
    
    def check_teacher_permissions(self):
        """Check if the current user is a teacher"""
        teacher = self.get_teacher()
        if not teacher:
            return Response(
                {"error": "Only teachers can access this endpoint"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return teacher
    
    def filter_by_teacher_courses(self, queryset, teacher):
        """Filter queryset by teacher's courses"""
        teacher_courses = teacher.courses.all()
        return queryset.filter(course__in=teacher_courses)


class TeacherExamListCreateView(TeacherPermissionMixin, generics.ListCreateAPIView):
    queryset = Exam.objects.all()
    serializer_class = TeacherExamSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['related_to', 'is_active','course' , 'course__teacher' ,'unit', 'video', 'type','created','start','end','allow_show_results_at']
    search_fields = ['title', 'description','course__name' , 'course__teacher__name', 'unit__name', 'video__name']
    ordering_fields = ['start', 'end']

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Exam.objects.none()
        
        queryset = super().get_queryset()
        
        # Filter by teacher's courses
        queryset = queryset.filter(
            Q(unit__course__teacher=teacher) | Q(video__unit__course__teacher=teacher) | Q(course__teacher=teacher)
        )

        # Filter by status (existing logic)
        status_param = self.request.query_params.get("status")
        if status_param:
            now = timezone.now()
            if status_param == "soon":
                queryset = queryset.filter(start__gt=now)
            elif status_param == "active":
                queryset = queryset.filter(start__lte=now, end__gte=now)
            elif status_param == "finished":
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
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        if serializer.is_valid():
            try:
                # Check if teacher owns the course
                validated_data = serializer.validated_data
                course = None
                if 'unit' in validated_data and validated_data['unit']:
                    course = validated_data['unit'].course
                elif 'video' in validated_data and validated_data['video']:
                    course = validated_data['video'].unit.course
                elif 'course' in validated_data and validated_data['course']:
                    course = validated_data['course']
                
                if course and course.teacher != teacher:
                    return Response(
                        {"error": "You don't have permission to create exams for this course"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                exam = serializer.save()
                exam.clean()  # Trigger model validation
            except ValidationError as e:
                return Response({"errors": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherExamDetailView(TeacherPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Exam.objects.all()
    serializer_class = TeacherExamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Exam.objects.none()
        
        return super().get_queryset().filter(
            Q(unit__course__teacher=teacher) | Q(video__unit__course__teacher=teacher) | Q(course__teacher=teacher)
        )


#^ QuestionCategory 
class TeacherQuestionCategoryListCreateView(TeacherPermissionMixin, generics.ListCreateAPIView):
    queryset = QuestionCategory.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherQuestionCategorySerializer
    filterset_fields = ['course']

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return QuestionCategory.objects.none()
        
        return super().get_queryset().filter(course__teacher=teacher)

    def perform_create(self, serializer):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        if serializer.is_valid():
            course = serializer.validated_data.get('course')
            if course and course.teacher != teacher:
                return Response(
                    {"error": "You don't have permission to create categories for this course"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherQuestionCategoryRetrieveUpdateDestroyView(TeacherPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = QuestionCategory.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherQuestionCategorySerializer

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return QuestionCategory.objects.none()
        
        return super().get_queryset().filter(course__teacher=teacher)


#^ Question , Answer
class TeacherQuestionListCreateView(TeacherPermissionMixin, generics.ListCreateAPIView):
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherQuestionSerializer
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

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Question.objects.none()
        
        return super().get_queryset().filter(
            Q(course__teacher=teacher) | 
            Q(category__course__teacher=teacher) | 
            Q(unit__course__teacher=teacher) | 
            Q(video__unit__course__teacher=teacher)
        )

    def create(self, request, *args, **kwargs):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        try:
            # Extract basic question data
            question_data = {
                'text': request.data.get('text'),
                'points': request.data.get('points'),
                'difficulty': request.data.get('difficulty'),
                'category': request.data.get('category'),
                'video': request.data.get('video'),
                'unit': request.data.get('unit'),
                'question_type': request.data.get('question_type'),
                'comment': request.data.get('comment'),
            }

            # Handle question image
            if 'image' in request.FILES:
                question_data['image'] = request.FILES.get('image')

            # Check teacher permissions for related objects
            if question_data.get('category'):
                try:
                    category = QuestionCategory.objects.get(id=question_data['category'])
                    if category.course.teacher != teacher:
                        return Response(
                            {"error": "You don't have permission to create questions for this category"}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                except QuestionCategory.DoesNotExist:
                    pass

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
                
                answer_serializer = TeacherAnswerSerializer(data=answer_data)
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


class TeacherQuestionRetrieveUpdateDestroyView(TeacherPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = TeacherQuestionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Question.objects.none()
        
        return super().get_queryset().filter(
            Q(course__teacher=teacher) | 
            Q(category__course__teacher=teacher) | 
            Q(unit__course__teacher=teacher) | 
            Q(video__unit__course__teacher=teacher)
        )

    def patch(self, request, *args, **kwargs):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
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

                    answer_serializer = TeacherAnswerSerializer(answer, data=answer_data, partial=True)
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


class TeacherBulkQuestionCreateView(TeacherPermissionMixin, generics.CreateAPIView):
    queryset = Question.objects.all()
    serializer_class = TeacherQuestionSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        try:
            created_questions = []
            exam = None
            
            # Check if exam_id is provided and valid
            exam_id = request.data.get('exam_id')
            if exam_id:
                try:
                    exam = Exam.objects.get(id=exam_id)
                    # Check if teacher owns the exam
                    exam_course = None
                    if exam.unit:
                        exam_course = exam.unit.course
                    elif exam.video:
                        exam_course = exam.video.unit.course
                    elif exam.course:
                        exam_course = exam.course
                    
                    if exam_course and exam_course.teacher != teacher:
                        return Response(
                            {'error': 'You don\'t have permission to add questions to this exam'},
                            status=status.HTTP_403_FORBIDDEN
                        )
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
                        'question_type': request.data.get(f'questions[{q_index}][question_type]'),
                        'comment': request.data.get(f'questions[{q_index}][comment]'),
                    }

                    # Handle question image
                    image_key = f'questions[{q_index}][image]'
                    if image_key in request.FILES:
                        question_data['image'] = request.FILES[image_key]

                    # Check teacher permissions for category/course
                    if question_data.get('category'):
                        try:
                            category = QuestionCategory.objects.get(id=question_data['category'])
                            if category.course.teacher != teacher:
                                return Response(
                                    {'error': f'You don\'t have permission to create questions for category in question {q_index + 1}'},
                                    status=status.HTTP_403_FORBIDDEN
                                )
                        except QuestionCategory.DoesNotExist:
                            pass

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

                        answer_serializer = TeacherAnswerSerializer(data=answer_data)
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
class TeacherAnswerListCreateView(TeacherPermissionMixin, generics.ListCreateAPIView):
    queryset = Answer.objects.all()
    serializer_class = TeacherAnswerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question']

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Answer.objects.none()
        
        return super().get_queryset().filter(
            Q(question__course__teacher=teacher) | 
            Q(question__category__course__teacher=teacher) |
            Q(question__unit__course__teacher=teacher) |
            Q(question__video__unit__course__teacher=teacher)
        )

    def perform_create(self, serializer):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        if serializer.is_valid():
            question = serializer.validated_data.get('question')
            if question:
                # Check if teacher owns the question
                question_course = None
                if question.category:
                    question_course = question.category.course
                elif question.unit:
                    question_course = question.unit.course
                elif question.video:
                    question_course = question.video.unit.course
                
                if question_course and question_course.teacher != teacher:
                    return Response(
                        {"error": "You don't have permission to create answers for this question"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherAnswerRetrieveUpdateDestroyView(TeacherPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Answer.objects.all()
    serializer_class = TeacherAnswerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Answer.objects.none()
        
        return super().get_queryset().filter(
            Q(question__course__teacher=teacher) | 
            Q(question__category__course__teacher=teacher) |
            Q(question__unit__course__teacher=teacher) |
            Q(question__video__unit__course__teacher=teacher)
        )


#^ Essay Submission
class TeacherEssaySubmissionListView(TeacherPermissionMixin, generics.ListAPIView):
    queryset = EssaySubmission.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherEssaySubmissionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['exam', 'student', 'student__user', 'question','result_trial','is_scored']
    search_fields = ['student__name', 'exam__title']

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return EssaySubmission.objects.none()
        
        return super().get_queryset().filter(
            Q(exam__unit__course__teacher=teacher) |
            Q(exam__video__unit__course__teacher=teacher) |
            Q(exam__course__teacher=teacher)
        )


class TeacherScoreEssayQuestion(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = Question.objects.all()
    
    def post(self, request, submission_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        # Fetch the essay submission
        essay_submission = get_object_or_404(EssaySubmission, pk=submission_id)

        # Check if teacher owns the exam
        exam_course = None
        if essay_submission.exam.unit:
            exam_course = essay_submission.exam.unit.course
        elif essay_submission.exam.video:
            exam_course = essay_submission.exam.video.unit.course
        elif essay_submission.exam.course:
            exam_course = essay_submission.exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to score this essay"}, 
                status=status.HTTP_403_FORBIDDEN
            )

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
class TeacherQuestionCountView(TeacherPermissionMixin, APIView):
    """
    Endpoint to get the count of questions with details.
    Allows filtering by is_active, difficulty, category, video, unit, course, and question_type.
    """
    permission_classes = [IsAuthenticated]
    queryset = Question.objects.all()

    def get(self, request, *args, **kwargs):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        # Build filters dynamically
        filters = Q()
        
        # Filter by teacher's courses first
        teacher_filter = Q(
            Q(course__teacher=teacher) | 
            Q(category__course__teacher=teacher) |
            Q(unit__course__teacher=teacher) |
            Q(video__unit__course__teacher=teacher)
        )
        filters &= teacher_filter

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
class TeacherGetExamQuestions(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = Exam.objects.all()

    def get(self, request, exam_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        exam = get_object_or_404(Exam, pk=exam_id)

        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to view questions for this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        if exam.type == ExamType.RANDOM:
            return Response(
                {"message": "Random exam, I'll pick its questions randomly."},
                status=status.HTTP_200_OK
            )

        exam_questions = ExamQuestion.objects.filter(exam=exam).select_related('question')
        serializer = TeacherExamQuestionSerializer(exam_questions, many=True)

        return Response(
            {
                "exam_id": exam.id,
                "exam_title": exam.title,
                "questions": serializer.data
            },
            status=status.HTTP_200_OK
        )


#^ add questions to an exam (manual and bank)
class TeacherAddBankExamQuestionsView(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]  # Use JSONParser to parse JSON data
    queryset = Question.objects.all()

    def post(self, request, exam_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to add questions to this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the question IDs from the request
        question_ids = request.data.get("questions_ids", [])
        
        # Validate that question_ids is a list
        if not isinstance(question_ids, list):
            return Response(
                {"error": "Invalid format for question IDs. Expected a list of integers."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate the question IDs and check teacher permissions
        questions = Question.objects.filter(id__in=question_ids).filter(
            Q(course__teacher=teacher) | 
            Q(category__course__teacher=teacher) |
            Q(unit__course__teacher=teacher) |
            Q(video__unit__course__teacher=teacher)
        )
        
        invalid_ids = set(question_ids) - set(questions.values_list('id', flat=True))
        
        if invalid_ids:
            return Response(
                {"error": f"The following question IDs are invalid or you don't have permission: {list(invalid_ids)}"},
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


class TeacherAddManualExamQuestionsView(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    queryset = Question.objects.all()
    
    def post(self, request, exam_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to add questions to this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )

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

        # Use the TeacherQuestionSerializer to validate and create the question
        serializer = TeacherQuestionSerializer(data=question_data, context={'request': request})
        if serializer.is_valid():
            # Check if teacher owns the category/course
            category_id = question_data.get('category')
            if category_id:
                try:
                    category = QuestionCategory.objects.get(id=category_id)
                    if category.course.teacher != teacher:
                        return Response(
                            {"error": "You don't have permission to create questions for this category"}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                except QuestionCategory.DoesNotExist:
                    pass
                    
            question = serializer.save()
            ExamQuestion.objects.create(exam=exam, question=question)
            return Response(
                {"message": "Questions successfully created and added to the exam"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherRemoveExamQuestion(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = Question.objects.all()
    
    def delete(self, request, exam_id, question_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to remove questions from this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )

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
class TeacherGetRandomExamBank(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = ExamModel.objects.all()
    
    def get(self, request, exam_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to view random exam bank for this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate exam type
        if exam.type != ExamType.RANDOM:
            return Response(
                {"error": "This endpoint is only for random type exams"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the random exam bank
        random_exam_bank = get_object_or_404(RandomExamBank, exam=exam)
        serializer = TeacherRandomExamBankSerializer(random_exam_bank)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TeacherAddToRandomExamBank(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = ExamModel.objects.all()
    
    def post(self, request, exam_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to add questions to random exam bank for this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate exam type
        if exam.type != ExamType.RANDOM:
            return Response(
                {"error": "This endpoint is only for random type exams"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract and validate question IDs
        question_ids = request.data.get("question_ids", [])
        questions = Question.objects.filter(id__in=question_ids).filter(
            Q(course__teacher=teacher) | 
            Q(category__course__teacher=teacher) |
            Q(unit__course__teacher=teacher) |
            Q(video__unit__course__teacher=teacher)
        )

        if len(questions) != len(question_ids):
            return Response(
                {"error": "Some question IDs are invalid or you don't have permission"},
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
class TeacherExamModelListCreateView(TeacherPermissionMixin, generics.ListCreateAPIView):
    queryset = ExamModel.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherExamModelSerializer
    filterset_fields = ['is_active', 'exam']

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return ExamModel.objects.none()
        
        return super().get_queryset().filter(
            Q(exam__unit__course__teacher=teacher) |
            Q(exam__video__unit__course__teacher=teacher) |
            Q(exam__course__teacher=teacher)
        )

    def perform_create(self, serializer):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        if serializer.is_valid():
            exam = serializer.validated_data.get('exam')
            if exam:
                exam_course = None
                if exam.unit:
                    exam_course = exam.unit.course
                elif exam.video:
                    exam_course = exam.video.unit.course
                elif exam.course:
                    exam_course = exam.course
                
                if exam_course and exam_course.teacher != teacher:
                    return Response(
                        {"error": "You don't have permission to create exam models for this exam"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherExamModelRetrieveUpdateDestroyView(TeacherPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = ExamModel.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherExamModelSerializer

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return ExamModel.objects.none()
        
        return super().get_queryset().filter(
            Q(exam__unit__course__teacher=teacher) |
            Q(exam__video__unit__course__teacher=teacher) |
            Q(exam__course__teacher=teacher)
        )


#^ get examModel questions (he already added questions , to be reviewed by teacher )
class TeacherGetExamModelQuestions(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = ExamModel.objects.all()
    
    def get(self, request, exam_model_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        # Fetch the exam model
        exam_model = get_object_or_404(ExamModel, pk=exam_model_id)

        # Check if teacher owns the exam
        exam_course = None
        if exam_model.exam.unit:
            exam_course = exam_model.exam.unit.course
        elif exam_model.exam.video:
            exam_course = exam_model.exam.video.unit.course
        elif exam_model.exam.course:
            exam_course = exam_model.exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to view questions for this exam model"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch active questions for the exam model
        questions = [mq.question for mq in exam_model.model_questions.all()]

        # Serialize the questions
        serializer = TeacherQuestionSerializer(questions, many=True)

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
class TeacherRemoveQuestionFromExamModel(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = ExamModel.objects.all()
    
    def delete(self, request, exam_model_id, question_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        try:
            exam_model = get_object_or_404(ExamModel, pk=exam_model_id)
            
            # Check if teacher owns the exam
            exam_course = None
            if exam_model.exam.unit:
                exam_course = exam_model.exam.unit.course
            elif exam_model.exam.video:
                exam_course = exam_model.exam.video.unit.course
            elif exam_model.exam.course:
                exam_course = exam_model.exam.course
            
            if exam_course and exam_course.teacher != teacher:
                return Response(
                    {"error": "You don't have permission to remove questions from this exam model"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
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
class TeacherSuggestQuestionsForModel(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = ExamModel.objects.all()
    
    def get_random_questions(self, exam: Exam, related_questions) -> list:
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

    def get_related_questions(self, exam: Exam):
        """
        Get the related questions from the random exam bank.
        """
        random_exam_bank = RandomExamBank.objects.filter(exam=exam).first()
        if not random_exam_bank:
            raise ValidationError("No Available Random Bank for that Exam, please create one first.")
        return random_exam_bank.questions.all()

    def get(self, request, exam_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        try:
            # Fetch the exam
            exam = get_object_or_404(Exam, pk=exam_id)

            # Check if teacher owns the exam
            exam_course = None
            if exam.unit:
                exam_course = exam.unit.course
            elif exam.video:
                exam_course = exam.video.unit.course
            elif exam.course:
                exam_course = exam.course
            
            if exam_course and exam_course.teacher != teacher:
                return Response(
                    {"error": "You don't have permission to suggest questions for this exam"}, 
                    status=status.HTTP_403_FORBIDDEN
                )

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
            serializer = TeacherQuestionSerializer(random_questions, many=True)

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
class TeacherAddQuestionsToModel(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = ExamModel.objects.all()
    
    def post(self, request, exam_id, exam_model_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        try:
            # Get the Exam and ExamModel objects
            exam = get_object_or_404(Exam, pk=exam_id)
            exam_model = get_object_or_404(ExamModel, pk=exam_model_id, exam=exam)

            # Check if teacher owns the exam
            exam_course = None
            if exam.unit:
                exam_course = exam.unit.course
            elif exam.video:
                exam_course = exam.video.unit.course
            elif exam.course:
                exam_course = exam.course
            
            if exam_course and exam_course.teacher != teacher:
                return Response(
                    {"error": "You don't have permission to add questions to this exam model"}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate exam type
            if exam.type != ExamType.RANDOM:
                return Response(
                    {"error": "This endpoint is only for random type exams"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the question IDs from the request
            question_ids = request.data.get("question_ids", [])

            # Validate the question IDs and check teacher permissions
            questions = Question.objects.filter(id__in=question_ids).filter(
                Q(course__teacher=teacher) | 
                Q(category__course__teacher=teacher) |
                Q(unit__course__teacher=teacher) |
                Q(video__unit__course__teacher=teacher)
            )
            
            invalid_ids = set(question_ids) - set(questions.values_list('id', flat=True))
            if invalid_ids:
                return Response(
                    {"error": f"The following question IDs are invalid or you don't have permission: {list(invalid_ids)}"},
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
class TeacherResultListView(TeacherPermissionMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherResultSerializer
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

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Result.objects.none()
            
        submitted = self.request.query_params.get('submitted', None)
        
        # Base queryset filtered by teacher's courses
        queryset = Result.objects.filter(
            Q(exam__unit__course__teacher=teacher) |
            Q(exam__video__unit__course__teacher=teacher) |
            Q(exam__course__teacher=teacher)
        ).select_related(
            'exam', 'student', 'exam_model'
        ).prefetch_related(
            Prefetch('trials', queryset=ResultTrial.objects.order_by('-trial')),
            'exam__submissions',
            'exam__exam_questions',
            'exam_model__exam_model_questions'
        ).annotate(
            total_questions=Count('exam__exam_questions'),
            is_allowed_to_show_result=Case(
                When(exam__allow_show_results_at__lte=timezone.now(), then=True),
                default=False,
                output_field=BooleanField()
            )
        )

        # Only apply the complex filtering if submitted parameter is provided
        if submitted is not None:
            submitted = submitted.lower()
            if submitted in ('true', '1'):
                # Get results where the active trial is submitted
                queryset = queryset.filter(
                    Q(trials__trial=F('trial'), trials__student_submitted_exam_at__isnull=False) |
                    Q(
                        trials__trial=F('trial') - 1,
                        trials__student_submitted_exam_at__isnull=False
                    ) & ~Q(trials__trial=F('trial'), trials__student_submitted_exam_at__isnull=False)
                )
            elif submitted in ('false', '0'):
                # Get results where the current trial exists but isn't submitted
                queryset = queryset.filter(
                    trials__trial=F('trial'),
                    trials__student_submitted_exam_at__isnull=True
                ).exclude(
                    trials__trial=F('trial') - 1,
                    trials__student_submitted_exam_at__isnull=False
                )
        
        return queryset.distinct()


class TeacherReduceResultTrialView(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = Exam.objects.all()
        
    def post(self, request, result_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        result = get_object_or_404(Result, pk=result_id)
        
        # Check if teacher owns the exam
        exam_course = None
        if result.exam.unit:
            exam_course = result.exam.unit.course
        elif result.exam.video:
            exam_course = result.exam.video.unit.course
        elif result.exam.course:
            exam_course = result.exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to modify results for this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
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


class TeacherExamResultDetailView(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = Result.objects.all()

    def get(self, request, result_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        result = get_object_or_404(Result, pk=result_id)
        
        # Check if teacher owns the exam
        exam_course = None
        if result.exam.unit:
            exam_course = result.exam.unit.course
        elif result.exam.video:
            exam_course = result.exam.video.unit.course
        elif result.exam.course:
            exam_course = result.exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to view results for this exam"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
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

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            answer_data = self._build_mcq_answer_data(submission, question)
            student_answers.append(answer_data)

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = self._build_essay_answer_data(submission, question)
            student_answers.append(answer_data)

        # Fetch correct answers and questions
        questions = Question.objects.filter(
            exam_questions__exam=result.exam
        ).select_related('category').prefetch_related('answers').distinct()

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


class TeacherExamResultDetailForTrialView(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    queryset = Result.objects.all()

    def get(self, request, result_id, result_trial_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher

        # Fetch the result
        result = get_object_or_404(Result, pk=result_id)

        # Check if teacher owns the exam
        exam_course = None
        if result.exam.unit:
            exam_course = result.exam.unit.course
        elif result.exam.video:
            exam_course = result.exam.video.unit.course
        elif result.exam.course:
            exam_course = result.exam.course

        if exam_course and exam_course.teacher != teacher:
            return Response(
                {"error": "You don't have permission to view results for this exam"},
                status=status.HTTP_403_FORBIDDEN
            )

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

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            answer_data = self._build_mcq_answer_data(submission, question)
            student_answers.append(answer_data)

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = self._build_essay_answer_data(submission, question)
            student_answers.append(answer_data)

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


class TeacherResultTrialsView(TeacherPermissionMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherResultTrialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['submit_type']

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return ResultTrial.objects.none()
            
        result_id = self.kwargs['result_id']
        result = get_object_or_404(Result, id=result_id)
        
        # Check if teacher owns the exam
        exam_course = None
        if result.exam.unit:
            exam_course = result.exam.unit.course
        elif result.exam.video:
            exam_course = result.exam.video.unit.course
        elif result.exam.course:
            exam_course = result.exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return ResultTrial.objects.none()
            
        return result.trials.all().annotate(
            mcq_score=Sum('submissions__question__points', filter=models.Q(submissions__is_correct=True)),
            essay_score=Sum('essay_submissions__score', filter=models.Q(essay_submissions__is_scored=True))
        ).order_by('trial')


#^ get students who took the exam and those who didn't
class TeacherStudentsTookExamAPIView(TeacherPermissionMixin, generics.ListAPIView):
    serializer_class = TeacherFlattenedStudentResultSerializer
    permission_classes = [IsAuthenticated]
    queryset = Student.objects.all()
    
    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Student.objects.none()
            
        exam_id = self.kwargs['exam_id']
        exam = get_object_or_404(Exam, id=exam_id)

        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Student.objects.none()

        # Get the related course for the exam
        related_course_id = exam.get_related_course()
        if not related_course_id:
            return Student.objects.none()

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


class TeacherStudentsDidNotTakeExamAPIView(TeacherPermissionMixin, generics.ListAPIView):
    serializer_class = TeacherStudentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Student.objects.none()
            
        exam_id = self.kwargs['exam_id']
        exam = get_object_or_404(Exam, id=exam_id)

        # Check if teacher owns the exam
        exam_course = None
        if exam.unit:
            exam_course = exam.unit.course
        elif exam.video:
            exam_course = exam.video.unit.course
        elif exam.course:
            exam_course = exam.course
        
        if exam_course and exam_course.teacher != teacher:
            return Student.objects.none()

        # Get the related course for the exam
        related_course_id = exam.get_related_course()
        if not related_course_id:
            return Student.objects.none()

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


class TeacherExamsTakenByStudentAPIView(TeacherPermissionMixin, generics.ListAPIView):
    serializer_class = TeacherFlattenedExamResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Exam.objects.none()
            
        student_id = self.kwargs['student_id']
        student = get_object_or_404(Student, id=student_id)

        # Get exams taken by the student, filtered by teacher's courses
        exams_taken = Exam.objects.filter(
            result__student=student
        ).filter(
            Q(unit__course__teacher=teacher) |
            Q(video__unit__course__teacher=teacher) |
            Q(course__teacher=teacher)
        ).distinct()

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


class TeacherExamsNotTakenByStudentAPIView(TeacherPermissionMixin, generics.ListAPIView):
    serializer_class = TeacherExamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return Exam.objects.none()
            
        student_id = self.kwargs['student_id']
        student = get_object_or_404(Student, id=student_id)
        
        # Get active course subscriptions for the student, filtered by teacher
        student_course_subscriptions = CourseSubscription.objects.filter(
            student=student, 
            active=True,
            course__teacher=teacher
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


class TeacherCopyExamView(TeacherPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, exam_id):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        serializer = TeacherCopyExamSerializer(data=request.data)
        if serializer.is_valid():
            original_exam = get_object_or_404(Exam, pk=exam_id)
            
            # Check if teacher owns the original exam
            original_exam_course = None
            if original_exam.unit:
                original_exam_course = original_exam.unit.course
            elif original_exam.video:
                original_exam_course = original_exam.video.unit.course
            elif original_exam.course:
                original_exam_course = original_exam.course
            
            if original_exam_course and original_exam_course.teacher != teacher:
                return Response(
                    {"error": "You don't have permission to copy this exam"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            data = serializer.validated_data

            # Check if teacher owns the target course
            target_course = data.get('course')
            if target_course and target_course.teacher != teacher:
                return Response(
                    {"error": "You don't have permission to copy exam to this course"}, 
                    status=status.HTTP_403_FORBIDDEN
                )

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


class TeacherExamQuestionReorderAPIView(TeacherPermissionMixin, APIView):
    """
    APIView to reorder ExamQuestion instances.
    Expects a list of dictionaries, each containing 'exam_question' (ID)
    and 'new_order'.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        serializer = TeacherExamQuestionReorderSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    for item in serializer.validated_data:
                        exam_question_id = item['exam_question']
                        new_order = item['new_order']

                        try:
                            exam_question = ExamQuestion.objects.get(id=exam_question_id)
                            
                            # Check if teacher owns the exam
                            exam_course = None
                            if exam_question.exam.unit:
                                exam_course = exam_question.exam.unit.course
                            elif exam_question.exam.video:
                                exam_course = exam_question.exam.video.unit.course
                            elif exam_question.exam.course:
                                exam_course = exam_question.exam.course
                            
                            if exam_course and exam_course.teacher != teacher:
                                return Response(
                                    {"error": f"You don't have permission to reorder questions for ExamQuestion {exam_question_id}"}, 
                                    status=status.HTTP_403_FORBIDDEN
                                )
                            
                            exam_question.order = new_order
                            exam_question.save()
                        except ExamQuestion.DoesNotExist:
                            return Response(
                                {"detail": f"ExamQuestion with ID {exam_question_id} not found."},
                                status=status.HTTP_404_NOT_FOUND
                            )
                return Response({"detail": "ExamQuestions reordered successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"detail": f"An error occurred during reordering: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#^ < ==============================[ <- video quiz -> ]============================== > ^#

class TeacherVideoQuizListCreateAPIView(TeacherPermissionMixin, generics.ListCreateAPIView):
    queryset = VideoQuiz.objects.all()
    serializer_class = TeacherVideoQuizSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
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

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return VideoQuiz.objects.none()
        
        return super().get_queryset().filter(course__teacher=teacher)

    def perform_create(self, serializer):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return teacher
            
        if serializer.is_valid():
            course = serializer.validated_data.get('course')
            if course and course.teacher != teacher:
                return Response(
                    {"error": "You don't have permission to create video quizzes for this course"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherVideoQuizRetrieveUpdateDestroyAPIView(TeacherPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = VideoQuiz.objects.all()
    serializer_class = TeacherVideoQuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        teacher = self.check_teacher_permissions()
        if isinstance(teacher, Response):
            return VideoQuiz.objects.none()
        
        return super().get_queryset().filter(course__teacher=teacher)
