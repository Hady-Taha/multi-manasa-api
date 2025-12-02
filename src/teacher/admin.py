from django.contrib import admin
from .models import Teacher, TeacherCenterStudentCode, TeacherCourseCategory


@admin.register(TeacherCenterStudentCode)
class TeacherCenterStudentCodeAdmin(admin.ModelAdmin):
    search_fields = ['code']  # enables search by code
    list_display = ['teacher', 'student', 'code', 'available', 'updated', 'created']  # show fields in list view
    list_filter = ['available', 'teacher']  # optional: filter by teacher or availability


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']  # adjust fields as per your Teacher model
    search_fields = ['name']


@admin.register(TeacherCourseCategory)
class TeacherCourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']  # adjust as per your model
    search_fields = ['name']