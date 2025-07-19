from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from student.models import *
from invoice.models import *
from view.models import VideoView
from invoice.models import InvoiceItemType,InvoicePayStatus
from .models import *


@receiver(post_save, sender=Invoice)
def pay_course_point(sender, instance, created, **kwargs):
    if created and instance.pay_status == InvoicePayStatus.PAID:
        if instance.item_type == InvoiceItemType.COURSE:
            get_course = Course.objects.get(barcode=instance.item_barcode)
            StudentPoint.objects.create(
                student=instance.student,
                point_type="course_subscribe",
                points=get_course.points,
                points_note=f"Pay for {get_course.name}"
            )
            instance.student.points += get_course.points
            instance.student.save()


@receiver(post_save, sender=VideoView)
def video_view_point(sender, instance, created, **kwargs):
    if created and instance.counter >= 1:
        StudentPoint.objects.create(
            student=instance.student,
            point_type="watching_videos",
            points=instance.video.points,
            points_note=f"Watch {instance.video.name}"
        )
        student = instance.student
        student.points += instance.video.points
        student.save()


