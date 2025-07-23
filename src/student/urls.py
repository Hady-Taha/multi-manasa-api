from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    #* < ==============================[ <- Auth -> ]============================== > ^#
    path("sign-in/", views.StudentSignInView.as_view(), name="student_sign_in"),
    path("sign-up/", views.StudentSignUpView.as_view(), name="student_sign_up"),
    path("sign-out/", views.StudentSignOutView.as_view(), name="student_sign_out"),
    path("sign-center-code/", views.StudentSignCenterCodeView.as_view(), name="student_sign_center_code"),
    path("sign-center-teacher/", views.StudentSingCenterTeacher.as_view(), name="StudentSingCenterTeacher"),
    path("token-refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    #* < ==============================[ <- Reset Password  -> ]============================== > ^#
    path("request-reset-password/", views.RequestResetPasswordView.as_view(), name="request_password_reset"),
    path("verify-pin-code/", views.VerifyPinCodeView.as_view(), name="verify_pin_code"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset_password"),
    
    #* < ==============================[ <- PROFILE -> ]============================== > ^#
    path("profile/", views.StudentProfileView.as_view(), name="student_profile"),
    
    # Analysis
    path("analysis/", views.ProfileAnalysis.as_view(), name="student_profile"),
    
    # Favorite
    path('favorite/list/', views.StudentFavoriteListView.as_view(), name='favorite-list'),
    path('favorite/create/', views.StudentFavoriteCreateView.as_view(), name='favorite-create'),
    path('favorite/delete/<int:id>/', views.StudentFavoriteDeleteView.as_view(), name='favorite-delete'),
    
    
    #* < ==============================[ <- Invoices -> ]============================== > ^#
    path("invoices/list/", views.InvoicesListView.as_view(), name="student_courses"),

    #* < ==============================[ <- Subscriptions -> ]============================== > ^#
    path("subscription/course/list/", views.SubscriptionCourseListView.as_view(), name="student_courses"),
    path("subscription/videos/list/", views.SubscriptionVideoListView.as_view(), name="student_videos"),
    
    
    #* < ==============================[ <- View  -> ]============================== > ^#
    path("views/video/list/", views.ViewsVideoList.as_view(), name="video-views-list"),
    
    #* < ==============================[ <- Notification -> ]============================== > ^#
    path("notification-list", views.NotificationList.as_view(), name="notification-list"),

    

]
