from rest_framework import serializers
from student.models import Student,StudentLoginSession


class TeacherStudentSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source='user.username', read_only=True)
    year_name = serializers.CharField(source='year.name', read_only=True)
    type_education_name = serializers.CharField(source='type_education.name', read_only=True)
    class Meta:
        model = Student
        fields = [
            'id',
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




class TeacherStudentLoginSessionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model = StudentLoginSession
        fields = [
            'student_name',
            'ip_address',
            'os',
            'os_version',
            'browser',
            'browser_version',
            'city',
            'is_mobile',
            'is_tablet',
            'is_touch_capable',
            'is_pc',
            'is_bot',
            'created',
            'updated',
        ]
        read_only_fields = ['created', 'updated']
        
