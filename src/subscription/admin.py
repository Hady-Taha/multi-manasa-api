from django.contrib import admin
from .models import CourseSubscription,VideoSubscription,CourseCollectionSubscription
# Register your models here.
admin.site.register(CourseSubscription)
admin.site.register(VideoSubscription)
admin.site.register(CourseCollectionSubscription)