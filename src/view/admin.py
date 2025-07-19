from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(VideoView)

@admin.register(ViewSession)
class ViewSessionAdmin(admin.ModelAdmin):
    search_fields = ['session']  # enables searching by session in the admin
    list_display = ['session', 'view', 'watch_time', 'updated', 'created']  # optional: show more fields in the list view


admin.site.register(SessionAction)