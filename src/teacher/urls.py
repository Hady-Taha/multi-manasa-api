from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Authentication -> ]============================== > ^#
    path("sign-in/", views.TeacherSignInView.as_view(), name="student_sign_in"),
    path("sign-up/", views.TeacherSignUpView.as_view(), name="student_sign_up"),
    #* < ==============================[ <- Profile -> ]============================== > ^#
    path("profile/", views.TeacherProfileView.as_view(), name="student_profile"),
    #* < ==============================[ <- Course -> ]============================== > ^#
    path("course/my-courses/",views.CoursesListView.as_view(), name="my_course_view"),
    path("course/create/",views.CreateCourseView.as_view(), name="create_course_view"),
    path("course/update/<int:id>/", views.UpdateCourseView.as_view(), name="update_course_view"),
    path("course/delete/<int:id>/",views.DeleteCourseView.as_view(), name="delete_course_view"),
    #* < ==============================[ <- Unit -> ]============================== > ^#
    path('course/<int:course_id>/unit/create/', views.UnitCreateView.as_view(), name="unit-create"),
    path('course/<int:course_id>/unit/list/', views.UnitListView.as_view(), name="unit-list"),
    path('course/<int:course_id>/unit/update/<int:id>/', views.UnitUpdateView.as_view(), name="unit-update"),
    path('course/<int:course_id>/unit/delete/<int:id>/', views.UnitDeleteView.as_view(), name="unit-delete"),
]
