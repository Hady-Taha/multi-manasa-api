from rest_framework import serializers
from django.contrib.auth.models import User
from teacher.models import *

#* < ==============================[ <- Profile [Serializers]  -> ]============================== > ^#

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
        
#* < ==============================[ <- Auth [Serializers]  -> ]============================== > ^#


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
    


