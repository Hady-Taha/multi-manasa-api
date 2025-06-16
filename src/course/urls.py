from django.urls import path
from . import views
urlpatterns = [
    path("list/",views.ListCourseView.as_view(), name="list_course_view"),
    
]
