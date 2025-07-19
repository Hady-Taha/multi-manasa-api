from django.db import models
from student.models import *
from course.models import *
from subscription.models import CourseSubscription
from student.models import StudentMobileNotificationToken
from .utils import send_push_notification
# Create your models here.

class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text  
    
    
