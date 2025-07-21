from django.urls import path
from . import views

urlpatterns = [
    path('homepage/counts/', views.HomeCountsView.as_view(), name='home-counts'),
    path('homepage/teacher-category/', views.TeacherCategoryAnalysisView.as_view(), name='teacher-category-analysis'),
]
