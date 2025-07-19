import time
import requests
from django.db.models. signals import post_save,pre_save,pre_delete
from django.template.loader import render_to_string
from django.dispatch import receiver
from rest_framework import status
from django.conf import settings
from course.models import *
from student.models import *
from .models import *
from subscription.models import CourseSubscription,VideoSubscription
from core.utils import send_whatsapp_massage


@receiver(post_save, sender=Invoice)
def handle_subscription_on_payment(sender, instance, created, **kwargs):
    
    if instance.pay_status != InvoicePayStatus.PAID:
        return

    if instance.item_type == InvoiceItemType.COURSE:
        try:
            course = Course.objects.get(barcode=instance.item_barcode)
        except Course.DoesNotExist:
            return

        if not CourseSubscription.objects.filter(student=instance.student, course=course, active=True).exists():
            CourseSubscription.objects.create(
                student=instance.student,
                course=course,
                invoice=instance,
                active=True
            )


    elif instance.item_type == InvoiceItemType.VIDEO:
        try:
            video = Video.objects.get(barcode=instance.item_barcode)
        except Video.DoesNotExist:
            return

        if not VideoSubscription.objects.filter(student=instance.student, video=video, active=True).exists():
            VideoSubscription.objects.create(
                student=instance.student,
                video=video,
                invoice=instance,
                active=True
            )
