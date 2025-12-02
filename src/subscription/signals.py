import requests
from django.db.models. signals import post_save,pre_save,pre_delete
from django.dispatch import receiver
from django.conf import settings
from student.models import *
from .models import *

@receiver(post_save, sender=CourseSubscription)
def student_subscription_montada(sender, instance, created, **kwargs):
    if created and settings.MONTADA and instance.course.free == False:

        url = f"{settings.MONTADA_URL}/student/auth/sign-up/"
        data = {
            "username": instance.student.user.username,
            "name": instance.student.name,
            "year": instance.student.year.id,
        }
        headers = {
            "api-key": f"{settings.MONTADA_API_KEY}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print("Subscription sent to Montada successfully.")
        else:
            print("Failed to send subscription to Montada.")