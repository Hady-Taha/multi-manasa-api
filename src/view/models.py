from django.db import models
from student.models import Student
from course.models import *
# Create your models here.

class VideoView(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    counter = models.IntegerField(default=0)
    status = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def get_session_duration(self):
        duration = 0
        for i in self.viewsession_set.all():
            duration += i.watch_time

        return duration
    

class ViewSession(models.Model):
    session = models.CharField(max_length=150,blank=True, null=True)
    view = models.ForeignKey(VideoView,on_delete=models.CASCADE,blank=True, null=True)
    watch_time = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    


class SessionAction(models.Model):
    session = models.ForeignKey(ViewSession, on_delete=models.CASCADE)
    action = models.CharField(max_length=150,blank=True, null=True)
    time = models.IntegerField(default=0)
    note = models.CharField(max_length=150,blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)