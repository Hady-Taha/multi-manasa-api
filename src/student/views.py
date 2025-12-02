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
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.exceptions import ValidationError
from user_agents import parse
from view.models import VideoView,ViewSession
from teacher.models import TeacherCenterStudentCode
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
from .utils import *
from django.utils import timezone
# MODELS

#* < ==============================[ <- Authentication [Views] -> ]============================== > ^#

class StudentSignUpView(APIView):

    def post(self, request):
        
        serializer = StudentSignUpSerializer(data=request.data)

        if serializer.is_valid():
            # Save the valid data, creating a new student instance
            student = serializer.save()

            # Generate an access token for the associated user
            access_token = AccessToken.for_user(student.user)
            
            # Save access_token in model student
            student.jwt_token = f'Bearer {access_token}'
            student.save()
            
            # Return the access token in the response
            context = {
                "access_token": f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access_token}'
            }

            return Response(context,status=status.HTTP_200_OK)
        
        # If validation fails, return the errors in the response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentSignInView(APIView):
    
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
            
            # Store Token In Student Model
            student = user.student
            student.jwt_token = access_token
            student.save()
            self.store_login_log(request, student)
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



    def store_login_log(self, request, student):
        """
        Store or update vendor login log with user agent data.
        """
        user_agent_info = self.get_user_agent_info(request)

        login_log, created = StudentLoginSession.objects.get_or_create(
            student=student,
            ip_address=user_agent_info['ip'],
            os=user_agent_info['os'],
        )

        if created:
            for attr, value in user_agent_info.items():
                if hasattr(login_log, attr):
                    setattr(login_log, attr, value)
            login_log.save()

    def get_user_agent_info(self, request):
        """
        Extract user agent and device info from the request.
        """
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(user_agent_string)

        ip = self.get_client_ip(request)

        return {
            'ip': ip,
            'os': user_agent.os.family,
            'os_version': user_agent.os.version_string,
            'browser': user_agent.browser.family,
            'browser_version': user_agent.browser.version_string,
            'device': user_agent.device.family,
            'is_mobile': user_agent.is_mobile,
            'is_tablet': user_agent.is_tablet,
            'is_touch_capable': user_agent.is_touch_capable,
            'is_pc': user_agent.is_pc,
            'is_bot': user_agent.is_bot,
        }

    def get_client_ip(self, request):
        """
        Retrieve the client's IP address from request headers.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    

class StudentSignOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = request.user.student

        # Get the latest login session (or refine with IP if needed)
        session = StudentLoginSession.objects.filter(student=student).order_by('-created').first()
        if session:
            session.logout_time = timezone.now()
            session.save(update_fields=["logout_time"])

        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class StudentSignCenterCodeView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,*args, **kwargs):
        code = request.data.get("code")
        student = request.user.student

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



class StudentSingCenterTeacher(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self,request,*args, **kwargs):
        code = request.data.get("code")
        student = request.user.student
        try:
            code = TeacherCenterStudentCode.objects.get(code=code,available=True)
            code.available = False
            code.student = student
            code.save()
        
        except TeacherCenterStudentCode.DoesNotExist:
            return Response({"error":"the code does not exist or not available"},status=status.HTTP_400_BAD_REQUEST)
            
        return Response(status=status.HTTP_200_OK)





#* < ==============================[ <- Reset Password [Views]  -> ]============================== > ^#

#^ Step 1 
class RequestResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({"detail": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            get_student = Student.objects.get(user__username=username)
        except Student.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "The user not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is blocked
        block_key = f"reset_block_{username}"
        if cache.get(block_key):
            return Response({"error": "لقد وصلت إلى الحد الأقصى في تغير كلمة المرور . حاول مرة أخرى بعد ١٢ ساعة."},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Count how many times the user has requested a reset in the last 12 hours
        count_key = f"reset_count_{username}"
        request_count = cache.get(count_key, 0)

        if request_count >= 3:
            cache.set(block_key, True, timeout=21600)  # 6 hours = 21600 seconds
            cache.delete(count_key)  # Reset count to avoid unnecessary storage
            return Response({"error": "لقد وصلت إلى الحد الأقصى في ارسال الكود . حاول مرة أخرى بعد 6 ساعة. "},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Increment request count
        cache.set(count_key, request_count + 1, timeout=43200)  # Keep count for 12 hours

        # Generate a 6-digit PIN code
        pin_code = str(random.randint(100000, 999999))

        # Store the PIN code in cache for validation (valid for 30 minutes)
        cache.set(username, pin_code, timeout=60*30)

        # Send the PIN via WhatsApp
        req_send = send_whatsapp_massage(
            massage=f'كود تغير الباسورد يا {get_student.name} هو {pin_code}',
            phone_number=f'{username}'
        )

        return Response({"success": req_send['success']}, status=status.HTTP_200_OK)


#^ Step 2
class VerifyPinCodeView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        pin_code = request.data.get('pin_code')

        if not username or not pin_code:
            return Response({"massage": "Phone number and PIN code are required.","success":False}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the stored PIN code from cache
        stored_pin_code = cache.get(username)

        if stored_pin_code is None:
            return Response({"massage": "انتهت صلاحية الكود او وقت الكود","success":False}, status=status.HTTP_400_BAD_REQUEST)

        if stored_pin_code != pin_code:
            return Response({"massage": "كود خطأ","success":False}, status=status.HTTP_400_BAD_REQUEST)

        # If the PIN code is valid, reset the password or proceed with further actions
        return Response({"massage": "تم التحقق من كود PIN بنجاح.","success":True}, status=status.HTTP_200_OK)


#^ Step 3
class ResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        pin_code = request.data.get('pin_code')
        new_password = request.data.get('new_password')

        if not username or not pin_code or not new_password:
            return Response({"massage": "Phone number, PIN code, and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Use APIRequestFactory to create a compatible HttpRequest for VerifyPinCodeView
        factory = APIRequestFactory()
        verify_request = factory.post('',data={'username': username, 'pin_code': pin_code})
        

        # Call VerifyPinCodeView
        verify_response = VerifyPinCodeView.as_view()(verify_request)
        if verify_response.status_code != status.HTTP_200_OK:
            return verify_response  # Invalid PIN code

        # Reset the password (assuming User model is used)
        try:
            user = User.objects.get(username=username)  # Adjust this based on your model
        except User.DoesNotExist:
            return Response({"massage": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()
        cache.delete(username)
        return Response({"massage": "Password reset successfully.","success":True}, status=status.HTTP_200_OK)


#* < ==============================[ <- PROFILE [Views] -> ]============================== > ^#

class StudentProfileView(generics.RetrieveAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(
            Student.objects.select_related('user', 'type_education', 'year'),
            user=self.request.user
        )

# Analysis
class ProfileAnalysis(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Retrieve the student from the authenticated user
        student = request.user.student

        progress_data = self._get_student_progress_in_all_courses(student)
        exam_data = self._get_student_exam_progress(student)
        watch_time_data = self._get_student_total_watch(student)
        context = {
            "progress_in_all_courses": progress_data,
            "exam_progress": exam_data,
            "total_watch_time":watch_time_data,
        }
        return Response(context, status=status.HTTP_200_OK)

    def _get_student_progress_in_all_courses(self, student):
        # Query to get all subscribed courses for the student
        subscribed_courses = CourseSubscription.objects.filter(student=student).select_related('course')

        # Initialize counters for watched and total videos
        total_videos = 0
        watched_video = 0

        for subscription in subscribed_courses:
            course = subscription.course
            total_videos += Video.objects.filter(unit__course=course, pending=False).count()
            watched_video += VideoView.objects.filter(
                video__unit__course=course,
                student=student,
                counter__gt=0
            ).count()

        # Return the aggregated progress as a dictionary
        return {
            "watched_video": watched_video,
            "total_videos": total_videos
        }

    def _get_student_exam_progress(self, student):
        # Get all exams related to the student
        exams = Exam.objects.filter(results__student=student,is_active=True).distinct()
        # Get all subscribed courses for the student
        subscribed_courses = CourseSubscription.objects.filter(student=student).select_related('course')
        # Initialize counters
        total_exams_taken = 0
        total_exam_scores = 0
        total_student_scores = 0

        # Calculate the total number of exams that should be taken
        total_exams_should_be_taken = Exam.objects.filter(
            Q(start__lte=timezone.now(), end__gte=timezone.now()) | Q(end__lt=timezone.now()),
            unit__course__in=[subscription.course for subscription in subscribed_courses],is_active=True
        ).count() + Exam.objects.filter(
            Q(start__lte=timezone.now(), end__gte=timezone.now()) | Q(end__lt=timezone.now()),
            video__unit__course__in=[subscription.course for subscription in subscribed_courses]
        ,is_active=True).count()

        for exam in exams:
            result = Result.objects.filter(student=student, exam=exam).first()
            if result:
                active_trial = result.active_trial  # Fetch the active trial
                if active_trial:
                    total_exams_taken += 1
                    total_exam_scores += active_trial.exam_score  # Use exam_score from active_trial
                    total_student_scores += active_trial.score  # Use score from active_trial

        # Return the aggregated exam progress as a dictionary
        return {
            "total_exams_should_be_taken": total_exams_should_be_taken,
            "total_exams_taken": total_exams_taken,
            "total_exam_scores": total_exam_scores,
            "total_student_scores": total_student_scores,
        }

    def _get_student_total_watch(self,student):
        total_time = 0
        for i in ViewSession.objects.filter(view__student=student):
            total_time+= i.watch_time
        
        
        return total_time


# Favorite
class StudentFavoriteListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentFavoriteListSerializer

    def get_queryset(self):
        return StudentFavorite.objects.filter(student=self.request.user.student)


class StudentFavoriteCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentFavoriteCreateSerializer

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student)

    
class StudentFavoriteDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentFavoriteListSerializer  # Optional; used only for error messages
    lookup_field = 'id'

    def get_queryset(self):
        return StudentFavorite.objects.filter(student=self.request.user.student)



#* < ==============================[ <- Invoices [Views] -> ]============================== > ^#

class InvoicesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentInvoiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'sequence',
        ]
    
    def get_queryset(self):
        return Invoice.objects.filter(
            student=self.request.user.student
        ).order_by("-created")
    

#* < ==============================[ <- Subscriptions [Views] -> ]============================== > ^#

#*Courses
class SubscriptionCourseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSubscriptionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "course__id": ["exact"],          # filter by course id
        "course__category__id": ["exact"], # optional: filter by category id
        "course__teacher": ["exact"] 
        
    }

    def get_queryset(self):
        return CourseSubscription.objects.filter(
            student=self.request.user.student,
            active=True,
        )


#*Videos
class SubscriptionVideoListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoSubscriptionSerializer

    def get_queryset(self):
        return VideoSubscription.objects.filter(
            student=self.request.user.student,
            active=True,
            )


#* < ==============================[ <- Views [Views]  -> ]============================== > ^#


class ViewsVideoList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentVideoViewListSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]

    def get_queryset(self):
        return VideoView.objects.filter(student=self.request.user.student,counter__gte=1).order_by("-created")



#* < ==============================[ <- Notification [Views] -> ]============================== > ^#

class NotificationList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentNotificationSerializer
    filterset_fields = ['is_read']

    def get_queryset(self):
        student = self.request.user.student
        return (
            Notification.objects
            .select_related('student')  
            .only('id', 'text', 'is_read', 'created_at', 'student_id')  
            .filter(student=student)
            .order_by('is_read', '-created_at')
        )
    





