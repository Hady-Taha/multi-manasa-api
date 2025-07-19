from django.urls import path
from . import views
urlpatterns = [
    path('register-mobile-token/', views.RegisterMobileToken.as_view(), name='register_mobile_token'),
    path('register-device/', views.RegisterDevice.as_view(), name='register_device'),
    path('validation-data/', views.AppValidationData.as_view(), name='app_validation_data'),
]