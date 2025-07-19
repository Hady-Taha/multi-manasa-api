from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Categories -> ]============================== > ^#
    path("categories/list/", views.CourseCategoryListView.as_view(), name="CourseCategoryListView-users"),
    #* < ==============================[ <- Course -> ]============================== > ^#
    path("list/", views.CourseListView.as_view(), name="CourseListView"),
    path("details/<int:id>/", views.CourseDetailView.as_view(), name="Course_detail_view"),
    #* < ==============================[ <- Unit -> ]============================== > ^#
    path("unit/list/<int:course_id>/", views.UnitListView.as_view(), name="unit_list_view"),
    #* < ==============================[ <- Unit Content -> ]============================== > ^#
    path("unit/content/<int:unit_id>/", views.UnitContent.as_view(), name="unit_content"),
]
