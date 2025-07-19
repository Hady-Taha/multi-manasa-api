from django.contrib import admin
from .models import (
    CourseCategory, VideoFile, File, CourseCode, VideoCode,
    Course, Unit, Video
)
from subscription.models import CourseSubscription,VideoSubscription
from exam.models import Exam
from django.db.models import Count

class SubUnitInline(admin.TabularInline):
    model = Unit
    fk_name = 'parent'  # the ForeignKey field to filter subunits
    extra = 0
    fields = ('name', 'order', 'pending')  # customize as needed
    show_change_link = True

class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ('name', 'order', 'pending', 'free', 'ready')
    show_change_link = True


class FileInline(admin.TabularInline):
    model = File
    extra = 0
    fields = ('name', 'order', 'pending')
    show_change_link = True


class ExamInline(admin.TabularInline):
    model = Exam  # Replace with your actual exam model
    extra = 0
    fields = ('title',)  # Example fields
    show_change_link = True

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    pass

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    pass

@admin.register(CourseCode)
class CourseCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title', 'course', 'student', 'price', 'available', 'created')
    list_filter = ('available', 'course', 'student')
    search_fields = ('code', 'title', 'student__user__username', 'course__name')
    readonly_fields = ('code', 'created', 'updated')
    ordering = ('-created',)

@admin.register(VideoCode)
class VideoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'code', 'title', 'video', 'get_course_name',
        'student', 'price', 'available', 'created'
    )
    list_filter = ('available', 'course', 'student')
    search_fields = ('code', 'title', 'student__user__username', 'video__name', 'course__name')
    readonly_fields = ('created', 'updated')
    ordering = ('-created',)

    @admin.display(description='Course')
    def get_course_name(self, obj):
        return obj.course.name if obj.course else '-'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    search_fields = ('name', 'barcode')
    list_display = (
        'id', 'name', 'barcode',
        'unit_count', 'video_count', 'file_count',
        'active_subscription_count'
    )

    def unit_count(self, obj):
        return obj.units.count()
    unit_count.short_description = 'Unit Count'

    def video_count(self, obj):
        return Video.objects.filter(unit__course=obj).count()
    video_count.short_description = 'Video Count'

    def file_count(self, obj):
        return File.objects.filter(unit__course=obj).count()
    file_count.short_description = 'File Count'

    def active_subscription_count(self, obj):
        return CourseSubscription.objects.filter(course=obj, active=True).count()
    active_subscription_count.short_description = 'Active Subscriptions'



@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'get_course_name', 'order', 'pending',
        'subunit_count', 'video_count', 'file_count', 'exam_count'
    )
    list_filter = ('course',)
    inlines = [SubUnitInline, VideoInline, FileInline, ExamInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _video_count=Count('unit_videos', distinct=True),
            _file_count=Count('unit_files', distinct=True),
            _exam_count=Count('exams', distinct=True),
        )

    @admin.display(description='Course Name')
    def get_course_name(self, obj):
        return obj.course.name

    @admin.display(description='Subunits')
    def subunit_count(self, obj):
        return obj.subunits.count()

    @admin.display(description='Videos', ordering='_video_count')
    def video_count(self, obj):
        return obj._video_count

    @admin.display(description='Files', ordering='_file_count')
    def file_count(self, obj):
        return obj._file_count

    @admin.display(description='Exams', ordering='_exam_count')
    def exam_count(self, obj):
        return obj._exam_count

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'barcode', 'get_unit_name', 'get_course_name')
    list_filter = ('unit', 'unit__course')
    search_fields = ('name', 'barcode')

    @admin.display(description='Unit')
    def get_unit_name(self, obj):
        if obj.unit:
            if obj.unit.parent:
                return f"{obj.unit.name} (Subunit of {obj.unit.parent.name})"
            return obj.unit.name
        return '-'

    @admin.display(description='Course')
    def get_course_name(self, obj):
        if obj.unit and obj.unit.course:
            return obj.unit.course.name
        return '-'