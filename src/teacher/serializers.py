from rest_framework import serializers
from django.contrib.auth.models import User
from course.models import Course,Unit
from .models import *

#* < ==============================[ <- Profile  -> ]============================== > ^#

class TeacherProfileSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="user.username")
    class Meta:
        model = Teacher
        fields = [
            'user__username',
            'name',
            'government',
            'active',
        ]


class TeacherSignUpSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source='user.username', required=True)
    password = serializers.CharField(source='user.password', write_only=True, required=True)
    email = serializers.EmailField(source='user.email', required=False)  # Email is optional
    
    class Meta:
        model = Teacher
        fields = [
            'username', 
            'password', 
            'email',  
            'name',
            'government', 
        ]
    
    def validate(self, data):
        # Ensure username is not equal to parent_phone
        username = data['user']['username']
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})
        
        return data
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher
    
#* < ==============================[ <- Course -> ]============================== > ^#

class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'name',
            'description',
            'price',
            'category',
            'discount',
            'year',
            'cover',
            'promo_video',
            'eduction_type',
            'time',
            'free',
            'is_active',
            'is_center',
            'points',
        ]

class CoursesListViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

#* < ==============================[ <- Unit -> ]============================== > ^#

class UnitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = [ 
            'id',
            'name', 
            'description', 
            'price', 
            'discount', 
            'free', 
            'is_active',
            'order', 
            'parent',
        ]

    def validate_parent(self, parent):
        if parent is None:
            return parent

        # Get course from view context
        course_id = self.context['view'].kwargs.get('course_id')
        request = self.context['request']

        if parent.course.id != int(course_id):
            raise serializers.ValidationError("The parent unit must belong to the same course.")

        if parent.course.teacher != request.user.teacher:
            raise serializers.ValidationError("You do not have permission to assign this parent unit.")

        return parent


class UnitListSerializer(serializers.ModelSerializer):
    sub_units = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            'id',
            'name',
            'description',
            'price',
            'discount',
            'free',
            'is_active',
            'sub_units',
        ]

    def get_sub_units(self, obj):
        sub_units = obj.sub_units.all()
        return UnitListSerializer(sub_units, many=True).data
    

