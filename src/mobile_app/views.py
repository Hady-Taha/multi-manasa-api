import re
#REST LIB
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.test import APIRequestFactory
from rest_framework import generics
from rest_framework.filters import SearchFilter
from core.permissions import HasValidAPIKey
from student.models import Student,StudentMobileNotificationToken,StudentDevice
from django.shortcuts import get_object_or_404,render
from course.models import Course,Video
from subscription.models import CourseSubscription,VideoSubscription
from view.models import VideoView
# Create your views here.

#* < ==============================[ <- MobileToken -> ]============================== > ^#

class RegisterMobileToken(APIView):
    permission_classes = [IsAuthenticated,HasValidAPIKey]

    def post(self,request,*args, **kwargs):
        get_student = Student.objects.get(user=request.user)
        data = request.data
        token,create = StudentMobileNotificationToken.objects.get_or_create(
            student=get_student,
            token = data.get("token")
        )

        return Response(status=status.HTTP_201_CREATED)


#* < ==============================[ <- DeviceId -> ]============================== > ^#

class RegisterDevice(APIView):
    permission_classes = [IsAuthenticated,HasValidAPIKey]
    
    def post(self, request, *args, **kwargs):
        get_student = Student.objects.get(user=request.user)
        data = request.data

        device_id, create = StudentDevice.objects.get_or_create(
            student=get_student,
            device_id=data.get("device_id"),
            os = data.get("os", "Unknown"),
            name = data.get("name", "Unknown")
        )

        return Response(status=status.HTTP_201_CREATED)


#* < ==============================[ <- App Validation Data -> ]============================== > ^#


class AppValidationData(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = request.data.get("course_id")
        video_id = request.data.get("lesson_id")
        device_id = request.data.get("device_id")
        student = request.user.student
        course = get_object_or_404(Course, id=course_id)

        # check if the app last version
        """""
        build_number = str(request.data.get("build_number"))
        app_version = str(request.data.get("app_version"))

        if build_number != settings.BUILD_NUMBER or app_version != settings.APP_VERSION:
            return Response(
                {"message": "Please update the app to the latest version"},
                status=status.HTTP_426_UPGRADE_REQUIRED
            )
        
        # Validate count device 
        #get_devices = StudentDevice.objects.filter(student=request.user.student)
        #get_device = get_devices.filter(device_id=device_id).first()
        #if get_devices.count() >= student.device_count and get_device not in get_devices:
        #    # If the student has exceeded the maximum number of devices allowed
        #    # Return an error response
        #    
        #    return Response(
        #        {"error": "You have exceeded the maximum number of devices allowed"},
        #        status=status.HTTP_403_FORBIDDEN
        #    )
        """""


        # Validate required parameters
        # if not course_id or not video_id:
        #     return Response(
        #         {"error": "course_id and video_id are required"},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )


        # Verify subscription
        # if not self._has_active_subscription(student, course):
        #     return Response(
        #         {"error": "You do not have access permissions"},
        #         status=status.HTTP_401_UNAUTHORIZED,
        #     )

        # Access video and handle response
        # video_response = self._access_video(course, video_id, student)
        # if video_response:
        #     return video_response

        return Response({"message": "video access granted"}, status=status.HTTP_200_OK)

    def _has_active_subscription(self, student, course):
        course_subscription = CourseSubscription.objects.filter(
            student=student, course=course, active=True
        ).exists()

        video_subscription = VideoSubscription.objects.filter(
            student=student, video__unit__course=course, active=True
        ).exists()

        return course_subscription or video_subscription


    def _access_video(self, course, video_id, student):
        """
        Handle Video access logic.
        """
        video = get_object_or_404(Video, id=video_id)

        # Validate that the video belongs to the course
        # if video.unit.course != course:
        #     return Response(
        #         {"error": "This video does not belong to the specified course"},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        # Check if the video is pending
        if video.pending:
            return Response(
                {"error": "This video is pending and unavailable"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the student has exceeded the allowed views
        video_view, _ = VideoView.objects.get_or_create(student=student, video=video)
        if video_view.counter >= video.view:
            return Response(
                {"error": "You do not have remaining views for this video"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None 



#* < ==============================[ <- EMBED -> ]============================== > ^#


class VideoEmbed(APIView):
    YOUTUBE_REGEX = re.compile(
        r'^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/'
    )

    def get(self, request):
        video_url = request.query_params.get('video_url')
        auth_token = request.query_params.get("auth_token")
        video_id = request.query_params.get("video_id")

        # Detect iOS user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_ios = any(device in user_agent for device in ['iphone', 'ipad', 'ipod'])

        # Replace .mpd with .m3u8 for iOS devices
        if is_ios and video_url and video_url.endswith('manifest.mpd'):
            video_url = video_url.replace('manifest.mpd', 'master.m3u8')

        context = {
            "video_url": video_url,
            "auth_token": auth_token,
            "video_id": video_id,
        }

        if video_url and self.YOUTUBE_REGEX.search(video_url):
            return render(request, 'embed_youtube.html', context)
        return render(request, 'embed_player.html', context)