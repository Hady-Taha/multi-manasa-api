# Django lib
from django.conf import settings
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from datetime import timedelta
# RestFrameWork lib
from rest_framework import status
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
# Apps Models
from student.models import Student
from course.models import *
from subscription.models import CourseSubscription
from .models import *
import uuid
import requests

# Create your views here.

class ViewsProgress(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        video = get_object_or_404(Video, id=request.data.get("lesson_id"))
        student = request.user.student
        duration_second = int(video.duration)
        time_second = int(request.data.get("time_second"))
        manasa_percentage = int(settings.WATCHED_PERCENTAGE)
        watched_percentage = (time_second / duration_second) * 100
        session_id = request.data.get("session_id", None)
        
        # Get or Create VideoView
        video_view, video_view_created = VideoView.objects.get_or_create(
            video=video,
            student=student
        )


        # Update VideoView
        if watched_percentage >= manasa_percentage and video_view.status == 0:
            
            # Increase counter
            video_view.counter += 1
            video_view.status = 1

            # Increase video views
            get_video = video_view.video
            get_video.views += 1
            
            # Save
            get_video.save()
            video_view.save()


        # Update VideoView
        elif watched_percentage <= manasa_percentage:
            video_view.status = 0
            video_view.save()

    
        if session_id:
            # Get or Create ViewSession
            session,session_created = ViewSession.objects.get_or_create(
                session=session_id,
                view=video_view
            )

            session.watch_time = time_second
            session.save()


        return Response(request.data, status=status.HTTP_200_OK)
    





class RegisterSessionAction(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        session_id = request.data.get("session_id", None)
        action = request.data.get("action", None)
        note = request.data.get("note", None)
        time = int(request.data.get("time", 0))

        # Get or Create ViewSession
        session = get_object_or_404(ViewSession, session=session_id)

        # Create SessionAction
        session_action = SessionAction.objects.create(
            session=session,
            action=action,
            time=time,
            note=note
        )

        return Response(request.data, status=status.HTTP_200_OK)