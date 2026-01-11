from rest_framework import serializers
from subscription.models import *


class TeacherListStudentCourseSubscription(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source="student.id")
    student__name = serializers.CharField(source="student.name")
    student__type_education_name = serializers.CharField(source="student.type_education.name")
    student__type_education = serializers.IntegerField(source="student.type_education.id")
    student__code = serializers.CharField(source="student.code",allow_null=True)
    student__is_center = serializers.BooleanField(source="student.is_center")
    student__user__username = serializers.CharField(source="student.user.username")
    course__name = serializers.CharField(source="course.name")
    student__government = serializers.CharField(source="student.government")
    student__parent_phone = serializers.CharField(source="student.parent_phone")
    invoice__sequence = serializers.CharField(source="invoice.sequence",allow_null=True)
    year__name = serializers.CharField(source="student.year.name")
    class Meta:
        model = CourseSubscription
        fields = [
            'id',
            'student_id',
            'student__name',
            'student__user__username',
            'student__government',
            'student__type_education_name',
            'student__type_education',
            'student__parent_phone',
            'course__name',
            'year__name',
            'student__code',
            'student__is_center',
            'active',
            'invoice__sequence',
            'created'
        ]