from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Teacher -> ]============================== > ^#
    path("teacher/list/", views.TeacherListView.as_view(), name="student_course_category"),
    path("teacher/list/simple/", views.TeacherSimpleListView.as_view(), name="student_course_category"),
    #* < ==============================[ <- Categories -> ]============================== > ^#
    path("categories/list/", views.CourseCategoryListView.as_view(), name="CourseCategoryListView-users"),
    path("categories/list/simple/", views.CourseCategorySimpleListView.as_view(), name="CourseCategorySimpleListView-users"),
    #* < ==============================[ <- Course -> ]============================== > ^#
    path("list/", views.CourseListView.as_view(), name="CourseListView"),
    path("center/list/", views.CourseCenterListView.as_view(), name="CourseCenterListView"),

    path("details/<int:id>/", views.CourseDetailView.as_view(), name="Course_detail_view"),
    #* < ==============================[ <- Unit -> ]============================== > ^#
    path("unit/list/<int:course_id>/", views.UnitListView.as_view(), name="unit_list_view"),
    #* < ==============================[ <- Unit Content -> ]============================== > ^#
    path("unit/content/<int:unit_id>/", views.UnitContent.as_view(), name="unit_content"),
]
