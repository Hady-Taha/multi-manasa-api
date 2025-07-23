from rest_framework import serializers
from teacher.models import Teacher,TeacherCourseCategory,TeacherCenterStudentCode
from course.models import CourseCategory
from django.contrib.auth.models import User


class TeacherCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=True)
    password = serializers.CharField(source='user.password', write_only=True, required=True)
    email = serializers.EmailField(source='user.email', required=False)  # Email is optional
    name = serializers.CharField(required=True)
    course_categories = serializers.PrimaryKeyRelatedField(
        queryset=CourseCategory.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    class Meta:
        model = Teacher
        fields = [
            'name',
            'username', 
            'password',
            'photo',
            'info',
            'email',
            'government',
            'active',
            'course_categories',
        ]

    def validate(self, data):
        # Validate username ≠ parent_phone
        username = data['user']['username']
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        return data



    def create(self, validated_data):
        user_data = validated_data.pop('user')
        course_categories = validated_data.pop('course_categories', [])

        user = User.objects.create_user(**user_data)
        teacher = Teacher.objects.create(user=user, **validated_data)

        # Create TeacherCourseCategory entries
        for category in course_categories:
            TeacherCourseCategory.objects.create(teacher=teacher, course_category=category)

        return teacher


class TeacherListSerializer(serializers.ModelSerializer):
    course_categories = serializers.SerializerMethodField()
    course_count = serializers.SerializerMethodField()
    user__username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Teacher
        fields = [
            'id',
            'user__username',
            'name',
            'photo',
            'info',
            'jwt_token',
            'government',
            'course_count',
            'active',
            'created',
            'course_categories',
        ]
        
    def get_course_categories(self, obj):
        categories = TeacherCourseCategory.objects.filter(teacher=obj).values('course_category__id', 'course_category__name')
        return categories
    
    def get_course_count(self, obj):
        return obj.courses.count()
    
    

class TeacherUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    course_categories = serializers.PrimaryKeyRelatedField(
        queryset=CourseCategory.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Teacher
        fields = [
            'name',
            'username',
            'email',
            'photo',
            'info',
            'government',
            'active',
            'course_categories',
        ]

    def update(self, instance, validated_data):
        # Handle nested user fields
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Handle teacher fields
        for attr, value in validated_data.items():
            if attr != 'course_categories':
                setattr(instance, attr, value)

        # Handle course_categories
        course_categories = validated_data.get('course_categories')
        if course_categories is not None:
            # Clear existing categories
            TeacherCourseCategory.objects.filter(teacher=instance).delete()
            # Add new ones
            for category in course_categories:
                TeacherCourseCategory.objects.create(teacher=instance, course_category=category)

        instance.save()
        return instance
    


class TeacherCenterStudentCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherCenterStudentCode
        fields = '__all__'
        
