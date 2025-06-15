from django.urls import path
from . import views
urlpatterns = [
    path("list/",views.ListCourseView.as_view(), name="list_course_view"),
    path("create/",views.CreateCourseView.as_view(), name="create_course_view")
]
