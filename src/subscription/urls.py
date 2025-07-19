from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Course -> ]============================== > ^#
    path("course/unit/list/<int:course_id>/", views.CourseUnitListView.as_view(), name=""),
    path("course/access-unit/content/<int:unit_id>/", views.CourseAccessUnitContent.as_view(), name=""),
    path('course/access-content/<int:course_id>/<str:content_type>/<int:content_id>/',views.CourseAccessContent.as_view()),
    #* < ==============================[ <- Video -> ]============================== > ^#
    path('video/access-content/<int:video_id>/',views.VideoAccessContent.as_view()),
]
