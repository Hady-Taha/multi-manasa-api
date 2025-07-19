from django.contrib import admin
from .models import CourseSubscription,VideoSubscription
# Register your models here.
admin.site.register(CourseSubscription)
admin.site.register(VideoSubscription)