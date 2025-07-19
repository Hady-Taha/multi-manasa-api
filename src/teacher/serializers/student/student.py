from rest_framework import serializers
from student.models import Student
from subscription.models import CourseSubscription

class TeacherStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'