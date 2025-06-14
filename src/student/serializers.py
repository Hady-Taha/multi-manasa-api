from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import F, Count
from student.models import *


class StudentProfileSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="user.username")
    education_type_name = serializers.CharField(source="education_type.name")
    year_name = serializers.CharField(source="year.name")
    
    class Meta:
        model = Student
        fields = [
            'user__username',
            'name',
            'parent_phone',
            'education_type_name',
            'education_type',
            'year',
            'year_name',
            'government',
            'code',
            'points',
            'division',
            'is_center',
            'active',
            'block',
        ]



class StudentSignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=True)
    password = serializers.CharField(source='user.password', write_only=True, required=True)
    email = serializers.EmailField(source='user.email', required=False)  # Email is optional
    parent_phone = serializers.CharField(required=False)
    
    class Meta:
        model = Student
        fields = [
            'username', 'password', 'email',  
            'name', 'parent_phone', 'education_type',
            'division',
            'year', 'government', 
        ]
    
    def validate(self, data):
        # Ensure username is not equal to parent_phone
        username = data['user']['username']
        parent_phone = data['parent_phone']

        if parent_phone and username == parent_phone:
            raise serializers.ValidationError({"username": "Username cannot be the same as parent phone."})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})
        
        return data
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        student_wallet = StudentWallet.objects.create(student=student)
        return student