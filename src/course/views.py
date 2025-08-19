from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.conf import settings
from rest_framework.filters import SearchFilter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from exam.serializers import ExamSerializer
from .models import CourseCategory,Course,Unit
from .serializers import TeacherListSerializer,CourseCategorySerializer,CourseSerializer,UnitSerializer,VideoSerializer,FileSerializer,SubunitSerializer
from teacher.models import Teacher,TeacherCenterStudentCode,TeacherCourseCategory


#* < ==============================[ <- Teacher -> ]============================== > ^#

class TeacherListView(generics.ListAPIView):
    serializer_class = TeacherListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name','id']
    search_fields = ['name']

    def get_queryset(self):
        return Teacher.objects.filter(active=True)


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


#* < ==============================[ <- Categories -> ]============================== > ^#

class CourseCategoryListView(generics.ListAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']


class CourseCategorySimpleListView(generics.ListAPIView):
    def get(self,request,*args, ** kwargs):
        qr = CourseCategory.objects.all().values("id",'name')
        return Response(qr,status=status.HTTP_200_OK)


#* < ==============================[ <- Course -> ]============================== > ^#

class CourseListView(generics.ListAPIView):
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['teacher','year','category']
    search_fields = ['name', 'category__name']

    def get_queryset(self):
        # Base queryset
        queryset = Course.objects.filter(is_center=False)

        # Apply filters if the user is authenticated
        if self.request.user.is_authenticated:
            student = self.request.user.student
            year = student.year
            filters = {
                'year': year,
                'is_center': False if not student.is_center else True
                }

            queryset = Course.objects.filter(
                Q(**filters) &
                (Q(type_education=student.type_education) | Q(type_education_id=3))
            )

        return queryset


    def get_serializer_context(self):
        # Pass the request to the serializer context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CourseCenterListView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['teacher','category']

    def get_queryset(self):
        student = self.request.user.student
        teachers = TeacherCenterStudentCode.objects.filter(student=student).values_list("teacher")
        queryset = Course.objects.filter(is_center=True,year=student.year.id,teacher__in=teachers)
        return queryset



class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all() 
    serializer_class = CourseSerializer
    lookup_field = 'id' 

    def get_queryset(self):
        # Base queryset
        queryset = Course.objects.filter(is_center=False)

        # Apply filters if the user is authenticated
        if self.request.user.is_authenticated:
            student = self.request.user.student
            year = student.year
            filters = {
                'year': year,
                'is_center': False if not student.is_center else True
                }

            queryset = Course.objects.filter(
                Q(**filters) &
                (Q(type_education=student.type_education) | Q(type_education_id=3))
            )

        return queryset

    def get_serializer_context(self):
        # Pass the request to the serializer context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context





#* < ==============================[ <- Unit -> ]============================== > ^#

class UnitListView(generics.ListAPIView):
    serializer_class = UnitSerializer

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Unit.objects.filter(course_id=course_id,pending=False,parent=None).order_by("order")
    

#* < ==============================[ <- Unit Content -> ]============================== > ^#

class UnitContent(APIView):
    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Unit, id=unit_id)
        content = self.get_content(unit)
        return Response(content, status=status.HTTP_200_OK)

    def get_content(self, unit):
        videos = self.get_video(unit)
        files = self.get_files(unit)
        subunits = self.get_subunit(unit)
        exams = self.get_exams(unit)
        combined_content = self.combine_content(videos,files,subunits,exams)
        return combined_content

    def get_video(self, unit):
        videos = unit.unit_videos.filter(pending=False)
        return VideoSerializer(videos, many=True, context={'request': self.request}).data

    def get_files(self,unit):
        files = unit.unit_files.filter(pending=False)
        return FileSerializer(files, many=True, context={'request': self.request}).data
    
    def get_exams(self, unit):
        exams = unit.exams.filter(is_active=True)
        return ExamSerializer(exams, many=True, context={'request': self.request}).data
    
    def get_subunit(self, unit):
        subunits = unit.subunits.filter(pending=False)
        return SubunitSerializer(subunits, many=True, context={'request': self.request}).data


    def combine_content(self, videos, files, subunits, exams):
        combined_content = sorted(
            [{'content_type': 'video', **video} for video in videos] +
            [{'content_type': 'file', **file} for file in files] +
            [{'content_type': 'subunit', **subunit} for subunit in subunits] +
            [{'content_type': 'exam', **exam} for exam in exams],
            key=lambda x: x.get('order', 0)
        )
        return combined_content
    
