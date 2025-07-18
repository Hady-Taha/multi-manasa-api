import uuid
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
    pending = models.BooleanField(default=True)
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
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='units')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free = models.BooleanField(default=False)
    pending = models.BooleanField(default=True)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='sub_units')
    order = models.IntegerField(default=1) 
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
    
#*============================>Unit Content<============================#*

class StreamType(models.TextChoices):
    EASYSTREAM_ENCRYPTED = "easystream_encrypt", "easystream encrypted"
    EASYSTREAM_NOT_ENCRYPTED = "easystream_not_encrypted", "easystream not encrypted"
    YOUTUBE_HIDE = "youtube_hide", "youtube hide"
    YOUTUBE_SHOW = "youtube_show", "youtube show"
    VDOCIPHER = "vdocipher","vdocipher",
    VIMEO = "vimeo","vimeo",

class Video(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    unit = models.ForeignKey(Unit, related_name="unit_videos", on_delete=models.CASCADE)
    can_view = models.IntegerField(default=5)
    views = models.IntegerField(default=0)
    duration = models.IntegerField(blank=True, null=True)
    stream_type = models.CharField(max_length=24,choices=StreamType.choices)
    stream_link = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    publisher_date = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    can_buy =  models.BooleanField(default=False)
    free = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=5)
    barcode = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    embed = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - id :{self.id}'
    


class VideoFile(models.Model):
    name = models.CharField(max_length=50,blank=True, null=True)
    video = models.ForeignKey(Video, related_name="video_files", on_delete=models.CASCADE)
    file = models.FileField(upload_to='videos/files/',validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'File for {self.video.name} - {self.file.name}'
    


class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='videos/files/',validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    pending = models.BooleanField(default=False)
    unit = models.ForeignKey(Unit, related_name='unit_files', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.unit.name}'
    