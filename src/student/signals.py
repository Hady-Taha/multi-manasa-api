from django.db.models.signals import post_save,pre_save
from django.shortcuts import get_object_or_404
from django.dispatch import receiver
from .models import Student

# @receiver(post_save, sender=Student)
# def new_student(sender, instance, created, *args, **kwargs):
#     if created:
#         pass