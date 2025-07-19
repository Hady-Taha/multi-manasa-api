import random
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from student.models import Student
from course.models import Course,Video
from teacher.models import Teacher
# Create your models here.

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    course = models.ForeignKey(Course, blank=True, null=True,on_delete=models.CASCADE)
    expiration_date = models.DateTimeField(blank=True, null=True)
    usage_limit = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    used_by_students = models.ManyToManyField(Student ,blank=True, related_name="used_promo_codes")  
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.discount_percent}% off"

    def is_valid(self):
        """Check if the promo code is active, not expired, and has remaining uses."""
        if not self.is_active:
            return False
        if self.expiration_date and timezone.now() > self.expiration_date:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

class InvoicePayStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    EXPIRED = "expired" ,"Expired"

class InvoiceItemType(models.TextChoices):
    COURSE = "course", "Course"
    VIDEO = "video", "Video"

class InvoiceMethodPayType(models.TextChoices):
    CODE = "code", "Code"
    EASY_PAY = "easy_pay", "Easy Pay"
    MANUALLY = 'manually','Manually'
    FREE = "free","Free"

class Invoice(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    pay_status = models.CharField(max_length=10,choices=InvoicePayStatus.choices,default='pending')
    pay_method = models.CharField(max_length=10,choices=InvoiceMethodPayType.choices,)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE,blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sequence = models.CharField(max_length=14, unique=True, blank=True, null=True)
    pay_code = models.CharField(max_length=30,blank=True, null=True)
    easy_pay_sequence =  models.CharField(max_length=500,blank=True, null=True)
    pay_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    item_type = models.CharField(max_length=10,choices=InvoiceItemType.choices)
    item_barcode = models.CharField(max_length=255)
    item_name = models.CharField(max_length=255)
    item_price = models.CharField(max_length=255)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate a unique 14-digit number for sequence
        if not self.sequence:
            self.sequence = self.generate_sequence()
        super().save(*args, **kwargs)


    def generate_sequence(self):
        while True:
            number = ''.join(random.choices('0123456789', k=14))
            if not Invoice.objects.filter(sequence=number).exists():
                return f'{number}'

