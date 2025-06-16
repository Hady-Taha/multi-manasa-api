from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
from teacher.models import Teacher
from student.models import Year,EducationType,DivisionType
# Create your models here.


class CourseCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    

class Course(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE) 
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL,blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    cover = models.FileField(upload_to='covers', max_length=500,validators=[FileExtensionValidator(allowed_extensions=['png','jpg','jpeg','webp'])])
    promo_video = models.CharField(max_length=350,blank=True, null=True)
    eduction_type = models.ForeignKey(EducationType, blank=True, null=True, on_delete=models.CASCADE)
    time = models.IntegerField(default=0)
    free = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    is_center = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=5)
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.name} | teacher : {self.teacher.name}'
    
    def get_discounted_price(self):
        if self.discount > 0:
            discount_amount = (self.price * self.discount) / 100
            return max(0, self.price - discount_amount)
        return self.price

    def save(self, *args, **kwargs):
        # Only convert to WebP if the cover is not in the WebP format
        if self.cover and not self.cover.name.endswith('.webp'):
            try:
                # Open the image file and convert it to WebP format
                img = Image.open(self.cover)
                img = img.convert("RGB")  # Ensure compatibility with WebP

                webp_io = BytesIO()
                img.save(webp_io, format="WEBP", quality=85)

                # Create a new cover file with WebP extension
                webp_file = ContentFile(webp_io.getvalue())

                # Save the cover field with the WebP file
                self.cover.save(f"{self.cover.name.split('.')[0]}.webp", webp_file, save=False)

            except Exception as e:
                # Handle errors that might occur during image conversion
                print(f"Error converting image: {e}")
        
        # Call the save method once after all modifications
        super().save(*args, **kwargs)


class Unit(models.Model):
    # allows reverse lookup: parent.sub_units.all()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='sub_units')
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    def get_discounted_price(self):
        if self.discount > 0:
            discount_amount = (self.price * self.discount) / 100
            return max(0, self.price - discount_amount)
        return self.price
    
