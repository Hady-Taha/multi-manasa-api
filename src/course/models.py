import random
import re
import requests
import uuid
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from student.models import Student , Year,TypeEducation
from io import BytesIO
from PIL import Image
from teacher.models import Teacher
# Create your models here.

class CourseCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    

class Course(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL,blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    cover = models.FileField(upload_to='covers', max_length=500,validators=[FileExtensionValidator(allowed_extensions=['png','jpg','jpeg','webp'])])
    promo_video = models.CharField(max_length=350,blank=True, null=True)
    type_education = models.ForeignKey(TypeEducation, blank=True, null=True, on_delete=models.CASCADE)
    time = models.IntegerField(default=0)
    free = models.BooleanField(default=False)
    publisher_date = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(default=False)
    can_buy = models.BooleanField(default=True)
    is_center = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=5)
    barcode = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} | id : {self.id}'
    
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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='units')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subunits')
    order = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    publisher_date = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        if self.parent:
            return f"Subunit: {self.name} (Parent: {self.parent.name})"
        return f"Unit: {self.name}"
    

#*============================>Unit Content<============================#*

class StreamType(models.TextChoices):
    EASYSTREAM_ENCRYPTED = "easystream_encrypt", "easystream encrypted"
    EASYSTREAM_NOT_ENCRYPTED = "easystream_not_encrypted", "easystream not encrypted"
    YOUTUBE_HIDE = "youtube_hide", "youtube hide"
    YOUTUBE_SHOW = "youtube_show", "youtube show"
    VDOCIPHER = "vdocipher","vdocipher",
    VIMEO = "vimeo","vimeo",


class PlayerType(models.TextChoices):
    MEDIA_KIT = "media_kit", "media kit"
    BETTER_PLAYER = "better_player", "better player"
    EMBED = "embed", "embed"


class Video(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    unit = models.ForeignKey(Unit, related_name="unit_videos", on_delete=models.CASCADE)
    can_view = models.IntegerField(default=5)
    views = models.IntegerField(default=0)
    duration = models.IntegerField(blank=True, null=True)
    stream_type = models.CharField(max_length=24,choices=StreamType.choices)
    stream_link = models.CharField(max_length=255)
    player_type = models.CharField(max_length=24,choices=PlayerType.choices,default=PlayerType.BETTER_PLAYER)
    vdocipher_id = models.CharField(max_length=255,blank=True, null=True)
    easystream_video_id = models.CharField(max_length=255,blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    publisher_date = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    can_buy =  models.BooleanField(default=False)
    free = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=5)
    is_depends = models.BooleanField(default=False)
    barcode = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    embed = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - id :{self.id}'

    def assign_teacher_if_missing(self):
        """Assign teacher from the related course if not set."""
        if not self.teacher:
            self.teacher = self.unit.course.teacher

    def fetch_stream_link_if_needed(self):
        """Fetch full stream link if it's an EASYSTREAM_ENCRYPTED type without http(s) prefix."""
        if self.stream_type != StreamType.EASYSTREAM_ENCRYPTED:
            return

        if re.match(r'^https?://', self.stream_link):
            return

        try:
            url = f"https://stream.easy-tech.ai/video/video/get/?video_uid={self.stream_link}"
            headers = {'api-key': settings.EASY_STREAM_API_KEY}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            self.stream_link = data.get('stream_url')
            self.vdocipher_id = data.get('vdocipher_id')
            self.easystream_video_id = data.get('video_id')
        
        except requests.RequestException as e:
            raise ValidationError(f"Video metadata fetch failed: {e}")

    def save(self, *args, **kwargs):
        self.assign_teacher_if_missing()
        self.fetch_stream_link_if_needed()
        super().save(*args, **kwargs)


        

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
    

#*============================>CODES<============================#*

class CourseCode(models.Model):
    title = models.CharField(max_length=50,blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE,blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    code = models.CharField(max_length=11, unique=True,blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)



class VideoCode(models.Model):
    title = models.CharField(max_length=50,blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE,blank=True, null=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE,blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    code = models.CharField(max_length=11, unique=True,blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    