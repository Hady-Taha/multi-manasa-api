from django.db import models
from student.models import Student
from course.models import Course,Video,CourseCollection
from invoice.models import Invoice

# Create your models here.
class CourseSubscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, blank=True, null=True,on_delete=models.CASCADE )
    active = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.name} | {self.course.name} | {self.active} '
    

class VideoSubscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    video = models.ForeignKey(Video,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student} | {self.invoice.sequence}'

class CourseCollectionSubscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    collection = models.ForeignKey(CourseCollection,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student} | {self.invoice.sequence}'
