from django.urls import path
from . import views

urlpatterns = [
    #* < ==============================[ <- Report -> ]============================== > ^#
    # path('send-otp/', views.SendParentOTPView.as_view()),
    path('report/', views.ParentReportView.as_view()),
]

