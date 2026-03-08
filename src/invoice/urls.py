from django.urls import path
from . import views
urlpatterns = [
    path("create/",views.PayWithEasyPay.as_view(),name="easy-pay"),
    path("easy-pay-call-back/<str:api_key>/", views.EasyPayCallBack.as_view(), name="pay-with-easy-pay"),
    path("pay/code/",views.PayWithCode.as_view(),name="pay-code"),
    path("promo-code-present/<str:promo_code>/",views.GetPromoCodePercentView.as_view(),name="pay-code"),
]
