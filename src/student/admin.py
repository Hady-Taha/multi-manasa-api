from django.contrib import admin
from subscription.models import CourseSubscription,VideoSubscription
from .models import *
# Register your models here.
admin.site.register(Year)
admin.site.register(TypeEducation)
admin.site.register(StudentMobileNotificationToken)
admin.site.register(StudentDevice)
admin.site.register(StudentPoint)
admin.site.register(StudentLoginSession)
admin.site.register(StudentBlock)
admin.site.register(StudentFavorite)


@admin.register(StudentCenterCode)
class StudentCenterCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'student', 'available', 'created')
    search_fields = ('code', 'student__user__username', 'student__name')
    list_filter = ('available',)
    readonly_fields = ('code', 'created', 'updated')
    ordering = ('-created',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'user', 'year', 'type_education',
        'active', 'block', 'is_center', 'is_admin', 'points', 'device_count',
        'active_course_subs', 'active_video_subs',
    )
    list_filter = (
        'year', 'type_education', 'active', 'block', 'is_center', 'is_admin'
    )
    search_fields = (
        'name', 'user__username', 'user__email', 'code', 'parent_phone'
    )
    ordering = ('-created',)

    def active_course_subs(self, obj):
        return CourseSubscription.objects.filter(student=obj, active=True).count()
    active_course_subs.short_description = "Active Course Subs"

    def active_video_subs(self, obj):
        return VideoSubscription.objects.filter(student=obj, active=True).count()
    active_video_subs.short_description = "Active Video Subs"