from django.contrib import admin
from .models import Teacher,TeacherCenterStudentCode,TeacherCourseCategory
# Register your models here.
admin.site.register(Teacher)
admin.site.register(TeacherCourseCategory)
admin.site.register(TeacherCenterStudentCode)