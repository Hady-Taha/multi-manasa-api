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

#* < ==============================[ <- Report [Views] -> ]============================== > ^#

# class SendParentOTPView(APIView):
#     def post(self, request):
#         phone = request.data.get("phone")
#         if not phone:
#             return Response({"error": "Phone number is required"}, status=400)

#         # Check if a student with this parent phone exists
#         if not Student.objects.filter(parent_phone=phone).exists():
#             return Response({"error": "OTP not sent"}, status=400)

#         #  Generate and store OTP in Redis
#         otp = str(random.randint(100000, 999999))
#         cache.set(f"otp:{phone}", otp, timeout=300)  # 5 minutes

#         # Send the OTP via WhatsApp
#         send_whatsapp_massage(phone, f"رمز التحقق الخاص بك هو: {otp}")

#         return Response({"message": "OTP sent successfully"})


class ParentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hash_text = request.query_params.get("token") 
        data_split=hash_text.split("T")
        student = Student.objects.get(
            parent_phone=data_split[0],
            type_education_id=data_split[1],
            id = data_split[2]
            )
        data = ParentReportSerializer(student).data
        return Response(data,status=status.HTTP_200_OK)