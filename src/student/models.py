import random
import requests
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from dashboard.models import Staff
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User


# Create your models here.

class Year(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return  f'{self.name}  - id: {self.id}'
    

class TypeEducation(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return  f'{self.name}  - id: {self.id}'


class Student(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=50,blank=True, null=True)
    parent_phone = models.CharField(max_length=11,blank=True, null=True)
    type_education = models.ForeignKey(TypeEducation, null=True, on_delete=models.SET_NULL)
    year = models.ForeignKey(Year,null=True, on_delete=models.SET_NULL)
    points = models.IntegerField(default=1)
    division = models.CharField(max_length=50,blank=True, null=True)
    government = models.CharField(max_length=100,blank=True, null=True)
    jwt_token = models.CharField(max_length=1000, blank=True, null=True)
    active = models.BooleanField(default=True)
    block = models.BooleanField(default=False)
    code = models.CharField(max_length=50,blank=True, null=True)
    is_center = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    device_count = models.IntegerField(default=2)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} | {self.id}'
    

class StudentCenterCode(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    code = models.CharField(max_length=50,blank=True, null=True,unique=True)
    available = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.available} | {self.code}'

    def save(self, *args, **kwargs):
        # Generate a unique 14-digit number for sequence
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    

class StudentMobileNotificationToken(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True)
    token = models.CharField(max_length=1000, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student} | {self.token}'
    

class StudentDevice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True)
    device_id = models.CharField(max_length=1000, blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    os = models.CharField(max_length=150, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student} | {self.device_id}'
    

class StudentLoginSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    os = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=100, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=150,blank=True, null=True)
    is_mobile = models.BooleanField(default=False)
    is_tablet = models.BooleanField(default=False)
    is_touch_capable = models.BooleanField(default=False)
    is_pc = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)
    logout_time = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.name} logged in from {self.ip_address}"


    def save(self, *args, **kwargs):
        # Only fetch if IP is set and location fields are empty
        if self.ip_address and not self.city:
            try:
                response = requests.get(f'https://ipapi.co/{self.ip_address}/json/')
                data = response.json()
                self.city = data.get('city')
            except Exception as e:
                pass
        super(StudentLoginSession, self).save(*args, **kwargs)


class StudentBlock(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reason = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class StudentPoint(models.Model):
    POINT_TYPE_CHOICES = [
        ('watching_videos', 'Watching videos'),
        ('submitting_answers', 'Submitting answers or assignments'),
        ('course_subscribe', 'Course subscribe'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_points")
    points_note = models.CharField(max_length=255,blank=True,null=True)
    point_type = models.CharField(max_length=50,choices=POINT_TYPE_CHOICES)
    points = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.point_type}"



class StudentFavorite(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='favorites')
    course = models.ForeignKey('course.Course',blank=True, null=True ,on_delete=models.SET_NULL)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    file = models.FileField(upload_to='student_favorites/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)



    class Meta:
        unique_together = ('student', 'content_type', 'object_id')
        ordering = ['-created']

    def __str__(self):
        return f"{self.student.name} - {self.content_object}"
    
    def save(self, *args, **kwargs):
        from course.models import File
        # Check if content_object is a File instance
        if isinstance(self.content_object, File):
            self.file = self.content_object.file
        else:
            self.file = None 
        super().save(*args, **kwargs)