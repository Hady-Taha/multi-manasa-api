import random
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
# Create your models here.

class Year(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return  f'{self.name}  - id: {self.id}'

class DivisionType(models.TextChoices):
    GENERAL = "general", "عام"
    SCIENCE = "science", "علمي علوم"
    MATH = "math", "علمي رياضة"
    LITERARY = "literary", "أدبي"

class EducationType(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return  f'{self.name}  - id: {self.id}'

class Student(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    parent_phone = models.CharField(max_length=11)
    education_type = models.ForeignKey(EducationType, null=True, on_delete=models.SET_NULL)
    year = models.ForeignKey(Year,null=True, on_delete=models.SET_NULL)
    points = models.IntegerField(default=1)
    division = models.CharField(max_length=20,choices=DivisionType.choices,default=DivisionType.GENERAL,blank=True,null=True)
    government = models.CharField(max_length=100)
    jwt_token = models.CharField(max_length=1000, blank=True, null=True)
    active = models.BooleanField(default=True)
    block = models.BooleanField(default=False)
    code = models.CharField(max_length=50,blank=True, null=True)
    is_center = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.name} | {self.id}'
    

class StudentWallet(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student} | {self.amount}'