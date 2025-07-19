from django.db import models
from student.models import Student,Year
# Create your models here.

class ExamCenter(models.Model):
    name = models.CharField(max_length=50,blank=True, null=True)
    lecture = models.CharField(max_length=50,blank=True, null=True)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    date = models.DateField(auto_now=False, auto_now_add=False,blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class ResultExamCenter(models.Model):
    student = models.ForeignKey(Student,blank=True, null=True ,on_delete=models.CASCADE)
    exam = models.ForeignKey(ExamCenter, on_delete=models.CASCADE ,blank=True, null=True)
    result_photo = models.CharField(max_length=550,blank=True, null=True)
    result_percentage = models.IntegerField(default=0)
    result_degree = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Center(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Lecture(models.Model):
    name = models.CharField(max_length=50,)
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    date = models.DateField() # "2024-03-20"
    status = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lecture', 'date')

