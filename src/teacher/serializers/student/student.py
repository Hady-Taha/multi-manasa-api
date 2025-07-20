from rest_framework import serializers
from student.models import Student
from subscription.models import CourseSubscription

class TeacherStudentSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source='user.username', read_only=True)
    year_name = serializers.CharField(source='year.name', read_only=True)
    type_education_name = serializers.CharField(source='type_education.name', read_only=True)
    class Meta:
        model = Student
        fields = [
            "name",
            "user__username",
            "parent_phone",
            "type_education_name",
            'type_education',
            "division",
            "government",
            'year_name',
            "year",
        ]













