import random
import datetime
import hashlib
# DJANGO LIB
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.exceptions import ValidationError
from user_agents import parse
from view.models import VideoView,ViewSession
#REST LIB
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.test import APIRequestFactory
from rest_framework import generics
from rest_framework.filters import SearchFilter
from exam.models import Result,Exam
# APP
from core.permissions import HasValidAPIKey
from core.utils import send_whatsapp_massage
from .models import *
from .serializers import *
from django.utils import timezone
# MODELS
from course.models import Course,CourseCategory
from teacher.models import Teacher


class HomeCountsView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        counts = {
            "total_courses": Course.objects.count(),
            "total_teachers": Teacher.objects.count(),
            "total_students": User.objects.filter(is_active=True).count(),
            "total_categories": CourseCategory.objects.count(),
        }
        return Response({"counts": counts}, status=status.HTTP_200_OK)

class TeacherCategoryAnalysisView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        teacher_in_category = CourseCategory.objects.annotate(
            total_teachers=Count('teachercoursecategory')
        ).filter(total_teachers__gt=0).values('name', 'total_teachers')

        return Response({"teacher_in_category": teacher_in_category}, status=status.HTTP_200_OK)