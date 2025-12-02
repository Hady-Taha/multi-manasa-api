from rest_framework import serializers
from course.models import Course,Video,File,Unit,VideoFile
from student.models import Student,StudentFavorite
from .models import CourseSubscription, VideoSubscription
from exam.models import Exam,Result
from view.models import VideoView
from django.contrib.contenttypes.models import ContentType

#* < ==============================[ <- Course Content -> ]============================== > ^#

class CourseUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'course', 'parent', 'order', 'created', 'updated']


#* Subunit
class CourseSubunitSerializer(serializers.ModelSerializer):
    sub_id = serializers.IntegerField(source='id')
    has_passed_exam = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = ['sub_id', 'name', 'order','has_passed_exam', 'created', 'updated']
    
    def get_has_passed_exam(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request.user, "student"):
            return False

        student = request.user.student

        # Get all prerequisite exams for this subunit (obj)
        dependent_exams = Exam.objects.filter(
            unit__course=obj.course,
            is_depends=True,
            order__lt=obj.order
        )

        for exam in dependent_exams:
            if exam.unit_id != obj.id:  # Skip exams belonging to the current subunit
                result = Result.objects.filter(student=student, exam=exam).first()
                if not result or not result.is_succeeded:
                    return False

        return True



#* Video
class CourseVideoFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoFile
        fields = ['id', 'name', 'file', 'created']

class CourseVideoSerializer(serializers.ModelSerializer):
    video_files = CourseVideoFileSerializer(many=True, read_only=True)
    exam = serializers.SerializerMethodField()
    has_passed_exam = serializers.SerializerMethodField()
    has_watched = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    is_watched = serializers.SerializerMethodField()
    favorite_id = serializers.SerializerMethodField()
    class Meta:
        model = Video
        fields = [
            'id',
            'name',
            'description',
            'can_view',
            'duration',
            'stream_type',
            'is_depends',
            'order',
            'unit',
            'points',
            'barcode',
            'has_passed_exam',
            'has_watched',
            'is_watched',
            'is_favorite',
            'favorite_id',
            'exam',
            'video_files',
            ]

    def get_exam(self, obj):
        # Get the first exam associated with the video, if it exists
        exam = obj.exams.first()
        if exam:
            return {
                'id': exam.id,
                'name': exam.title,
            }
        return None


    def get_has_passed_exam(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        student = request.user.student

        # Get all dependent exams in the same unit before this file's order
        dependent_exams = Exam.objects.filter(
            unit__course=obj.unit.course,
            order__lt=obj.order,
            is_depends=True
        )

        # Check if the student has passed all dependent exams
        if not dependent_exams.exists():
            return True

        for exam in dependent_exams:
            result = Result.objects.filter(student=student, exam=exam).first()
            if not result or not result.is_succeeded:
                return False

        return True

    def get_has_watched(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        student = request.user.student

        # Get all dependent videos in the same unit before this video's order
        dependent_videos = Video.objects.filter(
            unit__course=obj.unit.course,
            order__lt=obj.order,
            is_depends=True
        )

        # If no dependent videos, allow watching
        if not dependent_videos.exists():
            return True

        # Check if student watched all dependent videos
        for video in dependent_videos:
            watched = VideoView.objects.filter(
                student=student,
                video=video,
                counter__gte=1
            ).exists()
            if not watched:
                return False

        return True
    
    def get_is_watched(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        student = request.user.student

        # Check if student watched the video
        watched = VideoView.objects.filter(student=student,video=obj,counter__gte=1).exists()
        if not watched:
            return False

        return True
    
    def get_is_favorite(self, obj):
        request = self.context.get("request")
        student = getattr(request.user, "student", None)
        if not student:
            return False
        content_type = ContentType.objects.get_for_model(Video)
        return StudentFavorite.objects.filter(student=student, content_type=content_type, object_id=obj.id).exists()

    def get_favorite_id(self, obj):
        request = self.context.get("request")
        student = getattr(request.user, "student", None)
        if not student:
            return None
        content_type = ContentType.objects.get_for_model(Video)
        favorite = StudentFavorite.objects.filter(student=student, content_type=content_type, object_id=obj.id).first()
        return favorite.id if favorite else None


#* File
class CourseFileSerializer(serializers.ModelSerializer):
    has_passed_exam = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    favorite_id = serializers.SerializerMethodField()
    class Meta:
        model = File
        fields = [
            'id', 
            'name',
            'unit',
            'file',
            'order',
            'has_passed_exam',
            'is_favorite',
            'favorite_id',
            ]

    def get_has_passed_exam(self, obj):
        request = self.context.get('request')
        student = request.user.student

        # Get all dependent exams in the same unit before this file's order
        dependent_exams = Exam.objects.filter(
            unit__course=obj.unit.course,
            order__lt=obj.order,
            is_depends=True
        )

        # Check if the student has passed all dependent exams
        if not dependent_exams.exists():
            return True

        for exam in dependent_exams:
            result = Result.objects.filter(student=student, exam=exam).first()
            if not result or not result.is_succeeded:
                return False

        return True


    def get_is_favorite(self, obj):
        request = self.context.get("request")
        student = getattr(request.user, "student", None)
        if not student:
            return False
        content_type = ContentType.objects.get_for_model(File)
        return StudentFavorite.objects.filter(student=student, content_type=content_type, object_id=obj.id).exists()

    def get_favorite_id(self, obj):
        request = self.context.get("request")
        student = getattr(request.user, "student", None)
        if not student:
            return None
        content_type = ContentType.objects.get_for_model(File)
        favorite = StudentFavorite.objects.filter(student=student, content_type=content_type, object_id=obj.id).first()
        return favorite.id if favorite else None


#* < ==============================[ <- Video -> ]============================== > ^#

class VideoSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoSubscription
        fields = [
            'id', 
            'video', 
            'active', 
            'created', 
            'updated'
            ]
