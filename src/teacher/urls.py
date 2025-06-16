from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Authentication -> ]============================== > ^#
    path("sign-in/", views.TeacherSignInView.as_view(), name="student_sign_in"),
    path("sign-up/", views.TeacherSignUpView.as_view(), name="student_sign_up"),
    #* < ==============================[ <- Profile  -> ]============================== > ^#
    path("profile/", views.TeacherProfileView.as_view(), name="student_profile"),
    #* < ==============================[ <- Course  -> ]============================== > ^#
    path("course/my-courses/",views.CoursesListView.as_view(), name="my_course_view"),
    path("course/create/",views.CreateCourseView.as_view(), name="create_course_view"),
    path("course/update/<int:id>/", views.UpdateCourseView.as_view(), name="update_course_view"),
    path("course/delete/",views.DeleteCourseView.as_view(), name="delete_course_view"),
]
