from django.db import models
from django.contrib.auth.models import User
from student.models import Year,Student
# Create your models here.

class Teacher(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    government = models.CharField(max_length=100)
    jwt_token = models.CharField(max_length=1000, blank=True, null=True)
    active = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.name} | {self.id}'
    


class TeacherCourseCategory(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='teacher_course_categories')
    course_category = models.ForeignKey('course.CourseCategory', on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.course_category.name} | {self.teacher.name}'



class TeacherCenterStudentCode(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True)
    code = models.CharField(max_length=100, unique=True)
    available = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.teacher.name} | | {self.code} | {self.available} '
    
