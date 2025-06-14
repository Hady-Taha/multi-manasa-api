from django.contrib import admin
from .models import Year,Student,StudentWallet,EducationType
# Register your models here.
admin.site.register(Year)
admin.site.register(Student)
admin.site.register(StudentWallet)
admin.site.register(EducationType)