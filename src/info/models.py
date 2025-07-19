from django.db import models
from student.models import Year
# Create your models here.

class TeacherInfo(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='teacher_photo/',blank=True, null=True)
    info = models.TextField()
    facebook_link = models.URLField(max_length=200, blank=True, null=True)
    tiktok_link = models.URLField(max_length=200, blank=True, null=True)
    instagram_link = models.URLField(max_length=200, blank=True, null=True)
    youtube_link = models.URLField(max_length=200, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

#^======================Centers======================^#

class Center(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone_number = models.TextField()
    number_seats = models.IntegerField(default=0)
    government = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class TimingCenter(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    day = models.CharField(max_length=100)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.center.name} - {self.day}"
    

#^======================Books & Distributor ======================^#

class Book(models.Model):
    name = models.CharField(max_length=50)
    cover = models.ImageField(upload_to='book_cover/', blank=True, null=True) 
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Distributor(models.Model):
    name = models.CharField(max_length=50)
    phone_number = models.TextField(max_length=50)
    government = models.CharField(max_length=100)
    address = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class DistributorBook(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.name} - {self.distributor.name}"