from django.contrib.auth.models import User
from django.db.models import F, Count
from rest_framework import serializers
from student.models import *
from teacher.models import TeacherCenterStudentCode

class StudentSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="user.username")
    type_education__name = serializers.CharField(source="type_education.name")
    year__name = serializers.CharField(source="year.name")
    student_course_count = serializers.SerializerMethodField()
    class Meta:
        model = Student
        fields = [
            'id',
            'user__username',
            'name',
            'parent_phone',
            'division',
            'type_education',
            'type_education__name',
            'year',
            'points',
            'year__name',
            'government',
            'code',
            'jwt_token',
            'is_center',
            'active',
            'block',
            'points',
            'device_count',
            'student_course_count',
            'is_admin',
            'created'
        ]

    def get_student_course_count(self,obj):
        return obj.coursesubscription_set.filter(active=True).count()


class UpdateStudentSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source='user.username' ,required=False, allow_blank=True)
    name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    parent_phone = serializers.CharField(max_length=11, required=False, allow_blank=True)
    type_education = serializers.PrimaryKeyRelatedField(queryset=TypeEducation.objects.all(), required=False)
    year = serializers.PrimaryKeyRelatedField(queryset=Year.objects.all(), required=False)
    government = serializers.CharField(max_length=100, required=False, allow_blank=True)
    active = serializers.BooleanField(required=False)
    is_center = serializers.BooleanField(required=False)
    is_admin = serializers.BooleanField(required=False)

    class Meta:
        model = Student
        fields = [
            'user__username', 
            'name', 
            'parent_phone', 
            'type_education', 
            'year',
            'block',
            'government',
            'active', 
            'code',
            'device_count',
            'is_center', 
            'is_admin',
        ]


    def validate_block(self, value):
        """Ensure that block can only be set to False by the user."""
        if value is True:
            raise serializers.ValidationError("You are not allowed to set 'block' to True.")
        return value

    def update(self, instance, validated_data):
        # Update the user object (username)
        user_data = validated_data.pop('user', None)
        if user_data:
            username = user_data.get('username', None)
            if username:
                instance.user.username = username
                instance.user.save()


        # Handle the rest of the Student fields update
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the updated Student instance
        instance.save()
        return instance


class StudentPointSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.id')
    student_name = serializers.CharField(source='student.name')
    student_number = serializers.CharField(source='student.user.username')
    student_code = serializers.CharField(source='student.code')
    class Meta:
        model = StudentPoint
        fields = '__all__'


class StudentLoginSessionSerializer(serializers.ModelSerializer):
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


class StudentBlockSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name')
    student_id = serializers.CharField(source='student.id')
    student_user_username = serializers.CharField(source='student.user.username')
    staff_name = serializers.CharField(source='staff.name')
    class Meta:
        model = StudentBlock
        fields = [
            'student_name',
            'student_id',
            'student_user_username',
            'staff_id',
            'staff_name',
            'reason'
        ]

class StudentDeviceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name')
    class Meta:
        model = StudentDevice
        fields = [
            'id',
            'student',
            'student_name',
            'device_id',
            'name',
            'os'
        ]
        

class TeacherStudentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="student.id",allow_null=True)
    name = serializers.CharField(source="student.name",allow_null=True)
    username = serializers.CharField(source="student.user.username",allow_null=True)
    parent_phone = serializers.CharField(source="student.parent_phone",allow_null=True)
    type_education_id = serializers.IntegerField(source="student.type_education.id",allow_null=True)
    type_education_name = serializers.CharField(source="student.type_education.name",allow_null=True)
    year = serializers.IntegerField(source="student.year.id",allow_null=True)
    year_name = serializers.CharField(source="student.year.name",allow_null=True)
    division = serializers.CharField(source="student.division",allow_null=True)
    points = serializers.CharField(source="student.points",allow_null=True)
    
    class Meta:
        model = TeacherCenterStudentCode
        fields = [
            'id',
            'username',
            'name',
            'parent_phone',
            'type_education_id',
            'type_education_name',
            'year',
            'year_name',
            'points',
            'division',
            'code',
        ]