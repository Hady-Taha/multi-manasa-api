from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Authentication -> ]============================== > ^#
    path("sign-in/", views.TeacherSignInView.as_view(), name="student_sign_in"),
    path("sign-up/", views.TeacherSignUpView.as_view(), name="student_sign_up"),
    #* < ==============================[ <- Profile  -> ]============================== > ^#
    path("profile/", views.TeacherProfileView.as_view(), name="student_profile"),
]
