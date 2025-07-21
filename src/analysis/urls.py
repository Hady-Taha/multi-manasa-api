from django.urls import path
from . import views

urlpatterns = [
    path("homepage/", views.HomeAnalysisView.as_view(), name="home-analysis"),
]
