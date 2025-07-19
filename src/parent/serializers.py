from django.contrib.auth.models import User
from django.db.models import F, Count
from rest_framework import serializers
from student.models import *
from subscription.models import CourseSubscription,VideoSubscription
from course.models import Course,Video,File
from invoice.models import Invoice
from notification.models import Notification
from view.models import VideoView
from exam.models import *


#* < ==============================[ <- Report [serializers] -> ]============================== >


class CourseSubscriptionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name')

    class Meta:
        model = CourseSubscription
        fields = ['course_name', 'active']

class VideoViewSerializer(serializers.ModelSerializer):
    video_name = serializers.CharField(source='video.name')
    total_watch_time = serializers.SerializerMethodField()

    def get_total_watch_time(self, obj):
        return obj.get_session_duration()

    class Meta:
        model = VideoView
        fields = ['video_name', 'counter', 'total_watch_time']

class ResultTrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultTrial
        fields = [
            'trial', 'score', 'exam_score',
            'student_started_exam_at', 'student_submitted_exam_at', 'submit_type'
        ]


class ResultSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title')
    succeeded = serializers.SerializerMethodField()
    trials = ResultTrialSerializer(many=True)

    def get_succeeded(self, obj):
        return obj.is_succeeded

    class Meta:
        model = Result
        fields = ['exam_title', 'trial', 'succeeded', 'is_trials_finished', 'trials']


class CourseReportSerializer(serializers.Serializer):
    course_name = serializers.CharField()
    active = serializers.BooleanField()
    videos = VideoViewSerializer(many=True)
    results = ResultSerializer(many=True)


class ParentReportSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'user', 'name', 'parent_phone', 'points', 'division',
            'government', 'block', 'active', 'courses'
        ]

    def get_courses(self, student):
        subscriptions = student.coursesubscription_set.select_related('course')
        course_data = []

        for sub in subscriptions:
            course = sub.course

            # Get all videos in the course
            course_videos = Video.objects.filter(unit__course=course)

            # Get all watched videos (VideoView) by this student
            watched_views = {
                view.video_id: view
                for view in student.videoview_set.filter(video__unit__course=course)
            }

            # Combine: list of videos with watched status
            videos_output = []
            for video in course_videos:
                view = watched_views.get(video.id)
                if view and view.counter > 0:
                    videos_output.append({
                        "video_name": video.name,
                        "counter": view.counter,
                        "total_watch_time": view.get_session_duration(),
                        "watched": True
                    })
                else:
                    videos_output.append({
                        "video_name": video.name,
                        "watched": False
                    })

            # Get exam results
            results = student.result_set.filter(exam__course=course).prefetch_related('trials')

            # Calculate progress
            total_count = len(videos_output)
            watched_count = sum(1 for v in videos_output if v.get("watched"))
            progress_percent = int((watched_count / total_count) * 100) if total_count else 0
            
            course_data.append({
                'course_name': course.name,
                'active': sub.active,
                'videos': videos_output,
                'progress_percent':progress_percent,
                'results': ResultSerializer(results, many=True).data
            })

        return course_data