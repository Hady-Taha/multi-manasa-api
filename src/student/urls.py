from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Authentication -> ]============================== > ^#
    path("sign-in", views.StudentSignInView.as_view(), name="student_sign_in"),
    path("sign-up", views.StudentSignUpView.as_view(), name="student_sign_up"),
]
