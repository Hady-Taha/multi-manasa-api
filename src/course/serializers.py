from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id',
            'teacher',
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
            'pending',
            'is_center',
            'points',
        ]

