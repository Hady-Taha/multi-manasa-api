from rest_framework import serializers
from course.models import *
from subscription.models import CourseSubscription

#* < ==============================[ <- Course -> ]============================== > ^#

class TeacherListCourseSerializer(serializers.ModelSerializer):
    units_count = serializers.SerializerMethodField()
    videos_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    in_course_count = serializers.SerializerMethodField()
    year__name = serializers.CharField(source='year.name')
    category__name = serializers.CharField(source='category.name', allow_null=True)
    type_education_name = serializers.CharField(source='type_education.name', allow_null=True)
    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'description',
            'price',
            'discount',
            'year__name',
            'year',
            'cover',
            'category',
            'category__name',
            'type_education',
            'type_education_name',
            'promo_video',
            'time',
            'free',
            'pending',
            'barcode',
            'points',
            'is_center',
            'units_count',
            'videos_count',
            'files_count',
            'can_buy',
            'in_course_count',
            'publisher_date',
            'created',
        ]

    def get_units_count(self, obj):
        return obj.units.filter(parent=None).count()
    
    def get_videos_count(self, obj):
        return Video.objects.filter(unit__course=obj).count()
    
    def get_files_count(self, obj):
        return File.objects.filter(unit__course=obj).count()
    
    def get_in_course_count(self, obj):
        return CourseSubscription.objects.filter(course=obj).count()

class TeacherCreateCourseSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=CourseCategory.objects.all(), required=False, allow_null=True)
    class Meta:
        model = Course
        fields=[
            'name',
            'can_buy',
            'description',
            'price',
            'discount',
            'year',
            'cover',
            'promo_video',
            'publisher_date',
            'free',
            'pending',
            'is_center',
            'category',
            'type_education',
        ]

#* < ==============================[ <- Unit -> ]============================== > ^#

class TeacherSubunitSerializer(serializers.ModelSerializer):
    sub_id = serializers.IntegerField(source='id')
    
    class Meta:
        model = Unit
        fields = ['sub_id', 'description','name', 'order', 'created', 'pending','updated']


class TeacherListUnitSerializer(serializers.ModelSerializer):

    class Meta:
        model = Unit
        fields = [
            'id', 
            'name', 
            'course', 
            'description',
            'parent', 
            'order',
            'pending',
            'created',
            'updated'
            ]


class TeacherCreateUnitSerializer(serializers.ModelSerializer):

    class Meta:
        model = Unit
        fields = [
            'id',
            'name', 
            'order', 
            'parent',
            'course',
            'price',
            'description',
            'publisher_date',
            'pending',
            'created',
            'updated',
            ] 
    
    def validate(self, data):
        parent = data.get('parent')
        course = data.get('course')

        if course and self.context['request'].user.teacher != course.teacher:
            raise serializers.ValidationError({
                "course": "You are not the owner of this course."
            })

        if parent:
            if parent.parent:
                raise serializers.ValidationError({
                    "parent": "Nested subunits are not allowed. You can only create one level of subunits."
                })

        return data




#* < ==============================[ <- Content -> ]============================== > ^#

#* Video
class TeacherFileVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoFile
        fields = [
            'id',
            'name',
            'video',
            'file',
            'updated',
            'created',
        ]
        read_only_fields = ['video']


class TeacherListVideoSerializer(serializers.ModelSerializer):
    video_files = TeacherFileVideoSerializer(many=True, read_only=True)
    class Meta:
        model = Video
        fields = '__all__'


class TeacherCreateVideoSerializer(serializers.ModelSerializer):
    video_files = TeacherFileVideoSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Video
        fields = [
            'id',
            'name', 
            'description', 
            'unit', 
            'can_view',
            'duration',
            'stream_type', 
            'stream_link', 
            'order', 
            'price', 
            'pending', 
            'publisher_date',
            'can_buy', 
            'points',
            'video_files'
        ]
        read_only_fields = ['id', 'views', 'created', 'updated']

    
    def validate(self, data):
        unit = data.get('unit')
        
        if unit and self.context['request'].user.teacher != unit.course.teacher:
            raise serializers.ValidationError({
                "unit": "You are not the owner of the course this unit belongs to."
            })
        return data
    
    def create(self, validated_data):
        video_files_data = validated_data.pop('video_files', [])
        video = Video.objects.create(**validated_data)

        for file_data in video_files_data:
            VideoFile.objects.create(video=video, **file_data)

        return video


#* File
class TeacherListFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

    
    
class TeacherCreateFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['unit']
        
    def validate(self, data):
        unit = data.get('unit')
        if unit and self.context['request'].user != unit.course.teacher:
            raise serializers.ValidationError({
                "unit": "You are not the owner of the course this unit belongs to."
            })
        return data
