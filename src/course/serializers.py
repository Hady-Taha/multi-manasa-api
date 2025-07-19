from rest_framework import serializers
from subscription.models import CourseSubscription,VideoSubscription
from .models import *

#* < ==============================[ <- Category -> ]============================== > ^#

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = '__all__'

#* < ==============================[ <- Course -> ]============================== > ^#

class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    year__name = serializers.CharField(source='year.name', read_only=True)
    discounted_price = serializers.SerializerMethodField()
    units_count = serializers.SerializerMethodField()
    video_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    has_subscription = serializers.SerializerMethodField()
    course_duration = serializers.SerializerMethodField()
    category__name = serializers.CharField(source='category.name', allow_null=True)
    type_education__name = serializers.CharField(source='type_education.name', allow_null=True)
    class Meta:
        model = Course
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'name',
            'description',
            'price',
            'discounted_price',
            'category',
            'category__name',
            'year',
            'year__name',
            'cover',
            'promo_video',
            'units_count',
            'barcode',
            'can_buy',
            'video_count',
            'files_count',
            'has_subscription',
            'course_duration',
            'type_education',
            'type_education__name',
            'is_center',
            'time',
            'free',
            'created'
        ]

    def get_discounted_price(self, obj):
        
        if obj.discount > 0:
            discount_amount = (obj.price * obj.discount) / 100
            return max(0, obj.price - discount_amount)
        return obj.price

    def get_units_count(self, obj):
        return obj.units.filter(pending=False,parent=None).count()
    

    def get_course_duration(self, obj):
        duration = 0
        videos = Video.objects.filter(unit__course=obj,pending=False)
        for video in videos:
            if video.duration:
                duration+=video.duration
        return duration


    def get_video_count(self, obj):
        return Video.objects.filter(unit__course=obj, pending=False).count()

    def get_files_count(self, obj):
        return File.objects.filter(unit__course=obj,pending=False).count()

    def get_has_subscription(self, obj):
        # Get the request from the serializer context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if the student is subscribed to the course
            student = request.user.student
            return CourseSubscription.objects.filter(student=student, course=obj, active=True).exists()
        return False


#* < ==============================[ <- Unit -> ]============================== > ^#


class SubunitSerializer(serializers.ModelSerializer):
    sub_id = serializers.IntegerField(source='id')
    
    class Meta:
        model = Unit
        fields = ['sub_id', 'name', 'order', 'created', 'updated']

class UnitSerializer(serializers.ModelSerializer):
    subunits = SubunitSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = ['id', 'name', 'course', 'parent', 'order', 'subunits', 'created', 'updated']

#* < ==============================[ <- Unit Content -> ]============================== > ^#

#* Video
class VideoSerializer(serializers.ModelSerializer):
    video_files_count = serializers.SerializerMethodField()
    has_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id',
            'name',
            'description',
            'unit',
            'order',
            'duration',
            'video_files_count',
            'can_buy',
            'price',
            'points',
            'barcode',
            'created',
            'has_subscription',
        ]

    def get_video_files_count(self, obj):
        return obj.video_files.count()  

    def get_has_subscription(self, obj):
        # Get the request from the serializer context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if the student is subscribed to the course
            student = request.user.student
            
            return VideoSubscription.objects.filter(student=student, video=obj, active=True).exists()
        return False


#* File
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id', 
            'name',
            'unit',
            'order',
            ]
        

