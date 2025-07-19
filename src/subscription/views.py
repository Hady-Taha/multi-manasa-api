import requests
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import generics
from django.conf import settings
from rest_framework.response import Response
from django.shortcuts import render,get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from course.models import Course,Video,Unit,File,StreamType
from .utils import encrypt_data
from .models import CourseSubscription, VideoSubscription
from .serializers import *
from exam.serializers import ExamSerializer,VideoQuizSerializer
from exam.models import VideoQuiz

# Create your views here.
#* < ==============================[ <- Course -> ]============================== > ^#

#* Unit
class CourseUnitListView(generics.ListAPIView):
    serializer_class = CourseUnitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Unit.objects.filter(course_id=course_id,pending=False,parent=None).order_by("order")
    

#* Content
class CourseAccessUnitContent(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Unit, id=unit_id)
        student = request.user.student
        content = self.get_content(unit)
        
        if not CourseSubscription.objects.filter(student=student, course=unit.course, active=True).exists():
            return Response({"error": "You do not have access permissions"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(content, status=status.HTTP_200_OK)

    def get_content(self, unit):
        videos = self.get_video(unit)
        files = self.get_files(unit)
        subunits = self.get_subunit(unit)
        exam = self.get_exam(unit)
        combined_content = self.combine_content(videos,files,subunits,exam)
        return combined_content


    def get_video(self, unit):
        videos = unit.unit_videos.filter(pending=False)
        return CourseVideoSerializer(videos, many=True, context={'request': self.request}).data

    def get_files(self,unit):
        files = unit.unit_files.filter(pending=False)
        return CourseFileSerializer(files, many=True, context={'request': self.request}).data

    def get_exam(self,unit):
        exams = unit.exams.filter(is_active=True)
        return ExamSerializer(exams, many=True, context={'request': self.request}).data

    def get_subunit(self, unit):
        subunits = unit.subunits.filter(pending=False)
        return CourseSubunitSerializer(subunits, many=True, context={'request': self.request}).data


    def combine_content(self, videos, files, subunits, exams):
        combined_content = sorted(
            [{'content_type': 'video', **video} for video in videos] +
            [{'content_type': 'file', **file} for file in files] +
            [{'content_type': 'subunit', **subunit} for subunit in subunits] +
            [{'content_type': 'exam', **exam} for exam in exams],
            key=lambda x: x.get('order', 0)
        )
        return combined_content
    

class CourseAccessContent(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id, content_type, content_id, *args, **kwargs):
        student = request.user.student
        course = get_object_or_404(Course, id=course_id)
        
        # check if student have Course Subscription Access
        if not CourseSubscription.objects.filter(student=student, course=course, active=True).exists():
            return Response({"error": "You do not have access permissions"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # handel content type video
        if content_type == "video":
            return self.access_video(course,content_id,student)
        
        # handel content type file
        if content_type == "file":
            return self.access_file(course,content_id)

        
        return Response({"error":"content type not found "},status=status.HTTP_400_BAD_REQUEST)
    

    def access_video(self, course, video_id, student):
        video = get_object_or_404(Video, id=video_id)
        
        #^ validations on video
        # 1. validate if video in the same course
        if video.unit.course != course:
            return Response({"error": "This video does not belong to the specified course"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. validate if video is not pending
        if video.pending:
            return Response({"error": "This video is pending and unavailable"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. validate if this video have exam depends
        if not self.has_passed_required_exams(student, video):
            return Response({"error": "يجب عليك اجتياز جميع الامتحانات المطلوبة للدخول إلى هذا الدرس"}, status=status.HTTP_403_FORBIDDEN)
        

        #^ the video content
        # response video use stream type
        if video.stream_type in [StreamType.YOUTUBE_SHOW, StreamType.YOUTUBE_HIDE,StreamType.EASYSTREAM_NOT_ENCRYPTED,StreamType.VIMEO]:
            serializer = CourseVideoSerializer(video,context={'request': self.request})
            context={
                **serializer.data,
                "stream_link": video.stream_link
            }
            return Response(context, status=status.HTTP_200_OK)

        # EASYSTREAM APP
        if video.stream_type == StreamType.EASYSTREAM_ENCRYPTED:
            # the payload
            video_quizzes = VideoQuiz.objects.filter(video=video)
            payload = {
                "student_id": student.id,
                "course_id":course.id,
                "lesson_id": video.id,
                "video_id": video.id,
                "lesson_name": video.name,
                "unit_name": video.unit.name,
                "video_url": video.stream_link,
                "token": student.jwt_token,
                "base_url": settings.BASE_URL,
                "embed":video.embed,
                "platform_name": settings.PLATFORM_NAME,
                "request_delay": settings.REQUEST_DELAY,
                "exam_timeline": VideoQuizSerializer(video_quizzes, many=True, context={"request": self.request}).data if video_quizzes.exists() else None,
            }
            # encrypt the payload
            encrypted_data = encrypt_data(payload)
            # serve data to front
            serializer = CourseVideoSerializer(video,context={'request': self.request})
            context={
                "en_data": encrypted_data,
                **serializer.data
            }
            return Response(context,status=status.HTTP_200_OK)

        # VideoCipher
        if video.stream_type == StreamType.VDOCIPHER:
            response = requests.post(
                f"https://dev.vdocipher.com/api/videos/{video.stream_link}/otp",
                json={"ttl": 300},
                headers={
                    "Authorization": f"Apisecret {settings.VDO_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            return Response({**CourseVideoSerializer(video).data, "credentials": response.json()}, status=status.HTTP_200_OK)


    def access_file(self, course, file_id):
        file = get_object_or_404(File, id=file_id)
        # 1. validate if file in the same course
        if file.unit.course != course:
            return Response({"error": "This file does not belong to the specified course"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. validate if file is not pending
        if file.pending:
            return Response({"error": "This file is pending and unavailable"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CourseFileSerializer(file,context={'request': self.request})
        return Response(serializer.data,status=status.HTTP_200_OK)


    # Validations functions
    def has_passed_required_exams(self,student, video):
        dependent_exams = Exam.objects.filter(
            unit=video.unit, 
            order__lt=video.order, 
            is_depends=True
        )

        for exam in dependent_exams:
            result = Result.objects.filter(student=student, exam=exam).first()
            if not result or not result.is_succeeded:
                return False

        return True


#* < ==============================[ <- Video -> ]============================== > ^#

class VideoAccessContent(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,video_id,*args, **kwargs):
        
        video = Video.objects.get(id=video_id)
        student = request.user.student
        has_access = VideoSubscription.objects.filter(student=student,video=video,active=True ).exists()
        
        if not has_access:
            return Response({"detail": "Access denied. You are not subscribed to this video."}, status=status.HTTP_403_FORBIDDEN)

        return self.access_video(video_id, student)

    def access_video(self,video_id, student):
        video = get_object_or_404(Video, id=video_id)
        
        # 1. validate if video is not pending
        if video.pending:
            return Response({"error": "This video is pending and unavailable"}, status=status.HTTP_400_BAD_REQUEST)


        # response video use stream type
        if video.stream_type in [StreamType.YOUTUBE_SHOW, StreamType.YOUTUBE_HIDE,StreamType.EASYSTREAM_NOT_ENCRYPTED,StreamType.VIMEO]:
            serializer = CourseVideoSerializer(video,context={'request': self.request})
            context={
                **serializer.data,
                "stream_link": video.stream_link
            }
            return Response(context, status=status.HTTP_200_OK)

        if video.stream_type == StreamType.EASYSTREAM_ENCRYPTED:
            video_quizzes = VideoQuiz.objects.filter(video=video)
            payload = {
                "student_id": student.id,
                "lesson_id": video.id,
                "video_id": video.id,
                "lesson_name": video.name,
                "unit_name": video.unit.name,
                "video_url": video.stream_link,
                "token": student.jwt_token,
                "base_url": settings.BASE_URL,
                "platform_name": settings.PLATFORM_NAME,
                "request_delay": settings.REQUEST_DELAY,
                "exam_timeline": VideoQuizSerializer(video_quizzes, many=True, context={"request": self.request}).data if video_quizzes.exists() else None,
            }
            encrypted_data = encrypt_data(payload)
            serializer = CourseVideoSerializer(video,context={'request': self.request})
            context={
                "en_data": encrypted_data,
                **serializer.data
            }
            return Response(context,status=status.HTTP_200_OK)

        if video.stream_type == StreamType.VDOCIPHER:
            response = requests.post(
                f"https://dev.vdocipher.com/api/videos/{video.stream_link}/otp",
                json={"ttl": 300},
                headers={
                    "Authorization": f"Apisecret {settings.VDO_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            serializer = CourseVideoSerializer(video,context={'request': self.request})
            context={
                    **serializer.data, 
                    "credentials": response.json()
                }
            return Response(context, status=status.HTTP_200_OK)

