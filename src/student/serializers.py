from django.contrib.auth.models import User
from django.db.models import F, Count
from rest_framework import serializers
from student.models import *
from subscription.models import CourseSubscription,VideoSubscription
from course.models import Course,Video,File
from invoice.models import Invoice
from notification.models import Notification
from view.models import VideoView
from exam.models import *

#* < ==============================[ <- AUTH [serializers] -> ]============================== > ^#

class StudentSignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=True)
    password = serializers.CharField(source='user.password', write_only=True, required=True)
    email = serializers.EmailField(source='user.email', required=False)  # Email is optional
    parent_phone = serializers.CharField(required=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = Student
        fields = [
            'username', 'password', 'email',  
            'name', 'parent_phone', 'type_education',
            'division',
            'year', 'government', 
        ]

    def validate(self, data):
        # Validate username ≠ parent_phone
        username = data['user']['username']
        parent_phone = data.get('parent_phone')
        if parent_phone and username == parent_phone:
            raise serializers.ValidationError({"username": "Username cannot be the same as parent phone."})

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        # Validate type_education ID
        type_education = data.get('type_education')
        if type_education and type_education.id not in [1, 2]:
            raise serializers.ValidationError({"type_education": "Only type education with ID 1 or 2 is allowed."})

        return data



    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student


#* < ==============================[ <- PROFILE [serializers] -> ]============================== > ^#

class StudentProfileSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="user.username")
    type_education__name = serializers.CharField(source="type_education.name")
    year__name = serializers.CharField(source="year.name")
    
    class Meta:
        model = Student
        fields = [
            'user__username',
            'name',
            'parent_phone',
            'type_education',
            'type_education__name',
            'year',
            'year__name',
            'government',
            'code',
            'points',
            'division',
            'active',
            'block',
            'is_center',
            'is_admin'
        ]

# Favorite
class StudentFavoriteCreateSerializer(serializers.ModelSerializer):
    object_type = serializers.ChoiceField(choices=['video', 'exam', 'file'], write_only=True)
    object_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = StudentFavorite
        fields = ['course','object_type','object_id']

    def validate(self, attrs):
        object_type = attrs['object_type']
        object_id = attrs['object_id']

        model_map = {
            'video': Video,
            'exam': Exam,
            'file': File
        }

        model = model_map.get(object_type)
        if not model:
            raise serializers.ValidationError("Invalid object type.")

        try:
            content_object = model.objects.get(id=object_id)
        except model.DoesNotExist:
            raise serializers.ValidationError(f"{object_type} with id {object_id} does not exist.")

        attrs['content_type'] = ContentType.objects.get_for_model(model)
        attrs['object_id'] = content_object.id
        return attrs

    def create(self, validated_data):
        student = self.context['request'].user.student
        return StudentFavorite.objects.get_or_create(
            student=student,
            course = validated_data['course'],
            content_type=validated_data['content_type'],
            object_id=validated_data['object_id']
        )[0]


class StudentFavoriteListSerializer(serializers.ModelSerializer):
    object_id = serializers.IntegerField()
    object_type = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentFavorite
        fields = ['id', 'course','object_type', 'object_id', 'file','object_name', 'created']

    def get_object_type(self, obj):
        return obj.content_type.model

    def get_object_name(self, obj):
        return str(obj.content_object)


#* < ==============================[ <- Invoice [serializers] -> ]============================== > ^#

class StudentInvoiceSerializer(serializers.ModelSerializer):
    promo_code__code = serializers.CharField(source='promo_code.code', default=None)
    promo_code__discount_percent = serializers.CharField(source='promo_code.discount_percent', default='0')
    teacher_name = serializers.CharField(source='teacher.name', default=None)
    class Meta:
        model = Invoice
        fields = [
            'id',
            'teacher_name',
            'pay_status',
            'pay_method',
            'pay_code',
            'amount',
            'sequence',
            'item_type',
            'item_price',
            'item_name',
            'item_barcode',
            'expires_at',
            'promo_code__code',
            'promo_code__discount_percent',
            'created',
        ]


#* < ==============================[ <- Subscriptions [serializers] -> ]============================== > ^#

class CourseSubscriptionSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.id')
    course__name = serializers.CharField(source="course.name")
    course__cover = serializers.CharField(source="course.cover.url")
    course__description = serializers.CharField(source="course.description")
    units_course_count = serializers.SerializerMethodField()
    video_course_count = serializers.SerializerMethodField()
    files_course_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseSubscription
        fields = [
            'id',
            'course_id',
            'course__name',
            'course__cover',
            'course__description',
            'units_course_count',
            'video_course_count',
            'files_course_count',
            'active',
            'created',
        ]

    def get_units_course_count(self, obj):
        return obj.course.units.filter(pending=False).count()

    def get_video_course_count(self, obj):
        return Video.objects.filter(unit__course=obj.course, pending=False).count()

    def get_files_course_count(self, obj):
        return  File.objects.filter(unit__course=obj.course, pending=False).count()



class VideoSubscriptionSerializer(serializers.ModelSerializer):
    video_id = serializers.IntegerField(source="video.id")
    video_name = serializers.CharField(source="video.name")
    course_name = serializers.CharField(source="video.unit.course.name")
    
    class Meta:
        model = VideoSubscription
        fields = [
            'id',
            'video_id',
            'video_name',
            'course_name',
            'active',
            'active',
            'created',
        ]

#* < ==============================[ <- Views [serializers] -> ]============================== > ^#

class StudentVideoViewListSerializer(serializers.ModelSerializer):
    video__name = serializers.CharField(source="video.name")
    video_can_view = serializers.CharField(source="video.can_view")
    course_name = serializers.CharField(source="video.unit.course.name")
    total_watch_time = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoView
        fields=[
            'id',
            'video',
            'video__name',
            'video_can_view',
            'course_name',
            'counter',
            'total_watch_time',
            'updated',
            'created',
        ]
    
    
    def get_total_watch_time(self, obj):
        duration = 0
        for session in obj.viewsession_set.all():
            duration += session.watch_time
        return duration


#* < ==============================[ <- Notifications [serializers] -> ]============================== > ^#

class StudentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['text','is_read','created_at']

