from celery import shared_task
from course.models import *
from subscription.models import CourseSubscription
from .models import Notification
from .utils import send_push_notification

@shared_task
def notifications_custom_send(students_ids, text):
    students = Student.objects.filter(id__in=students_ids)

    for student in students:
        Notification.objects.create(
            student=student,
            text=text
        )
        
        send_push_notification(
            student=student,
            title="mr-khaled",
            body=text
            )
