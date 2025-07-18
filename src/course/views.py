import random
import datetime
# DJANGO LIB
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
#REST LIB
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.test import APIRequestFactory
from rest_framework import generics
from rest_framework.filters import SearchFilter
# FILES
from .models import *
from .serializers import *

class ListCourseView(generics.ListAPIView):
    queryset = Course.objects.filter(pending=False)
    serializer_class = CourseListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['year','category','teacher']
    search_fields = ['name','teacher__name']





