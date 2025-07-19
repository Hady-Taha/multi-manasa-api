from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import uuid

class Staff(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=50,blank=True, null=True)
    jwt_token = models.CharField(max_length=1000, blank=True, null=True)
    active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)



class RequestLog(models.Model):
    # Who made the request
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='request_logs'
    )
    request_id = models.CharField(max_length=36, default=uuid.uuid4, blank=True, null=True)
    # Anonymous users will be tracked by IP
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Request details
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)  # GET, POST, etc.
    view_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Request information
    # request_body = models.JSONField(null=True, blank=True)
    query_params = models.JSONField(null=True, blank=True)
    
    # Response information
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    request_body = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['method']),
            models.Index(fields=['status_code']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} ({self.user})"



