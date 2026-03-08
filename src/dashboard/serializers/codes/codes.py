from rest_framework import serializers
from course.models import CourseCode,VideoCode
from student.models import StudentCenterCode


#* < ==============================[ <- Course -> ]============================== > ^#

class CourseCodeSerializer(serializers.ModelSerializer):
    course__name = serializers.CharField(source="course.name",allow_null=True)
    student__name = serializers.CharField(source="student.name",allow_null=True)
    student__username = serializers.CharField(source="student.user.username",allow_null=True)
    class Meta:
        model = CourseCode
        fields = [
            'id', 
            'title', 
            'student',
            'student__name',
            'student__username',
            'course',
            "course__name",
            'price', 
            'code',
            'available'
        ]


#* < ==============================[ <- Video -> ]============================== > ^#

class VideoCodeSerializer(serializers.ModelSerializer):
    video__name = serializers.CharField(source="video.name")
    student__name = serializers.CharField(source="student.name", allow_null=True)
    video_id = serializers.CharField(source="video.id")
    
    class Meta:
        model = VideoCode
        fields = [
            'id', 
            'student', 
            "student__name",
            'video',
            "video__name",
            "video_id",
            'price', 
            'code',
            'available',
        ]



class StudentCenterCodeSerializer(serializers.ModelSerializer):
    student__name = serializers.CharField(source='student.name', allow_null=True )
    student__id = serializers.CharField(source='student.id', allow_null=True )
    student__username = serializers.CharField(source='student.user.username', allow_null=True )
    class Meta:
        model = StudentCenterCode
        fields = [
            'id', 
            'code', 
            'available', 
            'student__id',
            'student__username',
            'student__name',
        ]
