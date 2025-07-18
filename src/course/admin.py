from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(CourseCategory)
admin.site.register(Course)
admin.site.register(Unit)
admin.site.register(Video)
admin.site.register(VideoFile)
admin.site.register(File)