from django.urls import path
from . import views

urlpatterns = [
    path("views-progress", views.ViewsProgress.as_view(), name="ViewsProgress"),
    path("register-session-action", views.RegisterSessionAction.as_view(), name="RegisterSessionAction"),
]
