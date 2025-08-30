from django.conf import settings
from rest_framework import status
from django.db.models import OuterRef, Subquery, IntegerField, Value, F,Q
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.test import APIRequestFactory
from rest_framework import generics
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from student.models import Student
from course.models import *
from view.models import *
from exam.models import ResultTrial
from subscription.models import CourseSubscription
from core.pagination import CustomPageNumberPagination
from invoice.models import Invoice
from django.utils import timezone
from django.shortcuts import get_object_or_404 
from .serializers import *
from core.permissions import HasValidAPIKey
from teacher.models import TeacherCenterStudentCode,Teacher
from .models import *
from .filters import *
from datetime import datetime 
# Create your views here.

# Teacher
class TeacherSimpleListView(APIView):
    permission_classes = [HasValidAPIKey]
    def get(self, request,*args, **kwargs):
        teachers = Teacher.objects.values('id', 'name')
        return Response(list(teachers))


# Student
class TeacherStudentListView(generics.ListAPIView):
    permission_classes = [HasValidAPIKey]
    queryset = TeacherCenterStudentCode.objects.filter(available=False)
    serializer_class = TeacherStudentSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    throttle_classes = []
    filterset_fields =['teacher']

# Course
class CourseList(generics.ListAPIView):
    queryset = Course.objects.filter(is_center=True)
    serializer_class = CourseListSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []
    filterset_fields =['teacher']

# Video
class VideoList(generics.ListAPIView):
    queryset = Video.objects.filter(unit__course__is_center=True)
    serializer_class = VideoListSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []
    filterset_fields =['teacher']

# Video Views
class VideoViewsList(APIView):
    serializer_class = VideoViewSerializer
    permission_classes = [HasValidAPIKey]
    lookup_field = 'video_id'
    throttle_classes = []
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        video_id = self.kwargs.get('video_id')
        video = get_object_or_404(Video, id=video_id)
        course = video.unit.course

        # Get all students subscribed to the course
        subscriptions = CourseSubscription.objects.filter(course=course, active=True)
        students = [sub.student for sub in subscriptions]

        # Get VideoViews for the video
        video_views = VideoView.objects.filter(video=video, student__in=students)

        # Map existing views by student ID for quick lookup
        views_by_student_id = {lv.student_id: lv for lv in video_views}

        # Build final list (real or manual data for students without views)
        full_data = []
        for student in students:
            if student.id in views_by_student_id:
                full_data.append(views_by_student_id[student.id])
            else:
                # Manually create a dictionary for a non-viewed student
                full_data.append({
                    'video': video,
                    'student': student,
                    'total_watch_time': 0,
                    'status': 0,
                    'counter': 0,
                })

        # Paginate the data
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(full_data, request)
        
        # Serialize the paginated data
        serializer = self.serializer_class(result_page, many=True)

        # Return the paginated response
        return paginator.get_paginated_response(serializer.data)

# Course Views
class CourseViewsList(generics.ListAPIView):
    serializer_class = VideoViewSerializer
    permission_classes = [HasValidAPIKey]
    lookup_field = 'course_id'
    throttle_classes = []
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        course_id = self.kwargs.get(self.lookup_field)
        get_course = Course.objects.get(id=course_id)
        return VideoView.objects.filter(video__unit__course=get_course)

# Subscription
class SubscribeManyUsers(APIView):
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

    def post(self, request):
        data = request.data
        student_codes = data.get("codes", [])
        course = get_object_or_404(Course, id=data.get("course_id"))

        if not student_codes:
            return Response({"message": "No codes provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Chunk processing to avoid SQL limits
        chunk_size = 5000
        created_count = 0

        for i in range(0, len(student_codes), chunk_size):
            codes_chunk = student_codes[i : i + chunk_size]

            students = Student.objects.filter(code__in=codes_chunk)

            existing_ids = CourseSubscription.objects.filter(
                student__in=students, course=course, active=True
            ).values_list("student_id", flat=True)

            new_subscriptions = [
                CourseSubscription(student=student, course=course, active=True)
                for student in students if student.id not in existing_ids
            ]

            if new_subscriptions:
                CourseSubscription.objects.bulk_create(
                    new_subscriptions, ignore_conflicts=True, batch_size=5000
                )
                created_count += len(new_subscriptions)

        return Response(
            {"message": f"Success, created {created_count} subscriptions"},
            status=status.HTTP_200_OK,
        )


# Exam
class ExamList(generics.ListAPIView):
    permission_classes = [HasValidAPIKey]
    serializer_class = ExamSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ExamFilter   # <-- add this
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

    def get_queryset(self):
        return Exam.objects.filter(
            Q(unit__course__is_center=True) |
            Q(video__unit__course__is_center=True)
        )

class ExamResultList(generics.ListAPIView):
    permission_classes = [HasValidAPIKey]
    serializer_class = ExamResultSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

    def get_queryset(self):
        return Result.objects.filter(exam_id=self.kwargs.get('exam_id'),student__is_center=True)



class UnSubscribeManyUsers(APIView):
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

    def post(self, request):
        codes = request.data.get('codes', [])
        course_id = request.data.get('course_id')
        
        course = get_object_or_404(Course, id=course_id)
        students = Student.objects.filter(code__in=codes)
        
        subscriptions = CourseSubscription.objects.filter(student__in=students, course=course)
        updated_count = subscriptions.delete()
        
        return Response({'message': 'Success', 'deleted_count': updated_count}, status=status.HTTP_200_OK)

class SubmitResultCenterExam(APIView):
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

    def post(self, request, *args, **kwargs):  
        exam_name = request.data.get("exam_name")
        lecture_name = request.data.get("lecture_name")
        exam_date_raw = request.data.get("exam_date")
        exam_date = datetime.fromisoformat(str(exam_date_raw)).date() if exam_date_raw else None
        
        exam,create = ExamCenter.objects.get_or_create(
            name = exam_name,
            lecture = lecture_name,
            year_id = request.data.get("year")
        )

        exam.date = exam_date
        
        exam.save()

        for result in request.data.get("results", []):
            user_code = result.get('user_code')
            try:
                student = Student.objects.filter(code=user_code).first()
            except Student.DoesNotExist:
                continue  # Skip if student not found

            obj, created = ResultExamCenter.objects.get_or_create(
                exam=exam,
                student=student,
            )
            obj.result_percentage = result.get('result_percentage')
            obj.result_degree = result.get("result_degree")
            obj.result_photo = result.get('file_url')
            obj.save()

        return Response({"message": "Results processed."}, status=status.HTTP_200_OK)

#* =================================Center================================= *#

class CenterList(generics.ListAPIView):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

class CenterCreate(generics.CreateAPIView):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

#* =================================Lecture================================= *#

class LectureList(generics.ListAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

class LectureCreate(generics.CreateAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

#* =================================Attendance================================= *#

class AttendanceList(generics.ListAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []


class AttendanceCreate(APIView):
    permission_classes = [HasValidAPIKey]
    queryset = Attendance.objects.all()

    def post(self, request, *args, **kwargs):
        data = request.data
        lecture_name = data.get('lecture_name')
        attendance_status = data.get('status')
        date = data.get("date")
        students_codes = data.get('students_codes')

        lecture = get_object_or_404(Lecture, name=lecture_name)
        students_in = []
        skipped_students = []

        for code in students_codes:
            student = Student.objects.filter(code=code).first()  # Check if student exists

            if not student:
                skipped_students.append(code)  # Track skipped students
                continue  # Skip to the next iteration

            attendance, _ = Attendance.objects.update_or_create(
                student=student,
                lecture=lecture,
                date=date,
                defaults={'status': attendance_status}  # Use defaults for update_or_create
            )

            students_in.append(code)

        return Response(
            {
                "message": "Attendance processed successfully.",
                "students_marked": students_in,
                "students_skipped": skipped_students
            },
            status=status.HTTP_201_CREATED
        )