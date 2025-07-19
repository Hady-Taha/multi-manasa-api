from django.urls import path
from . import views
urlpatterns = [
    path('teacher-info/', views.TeacherInfoListView.as_view(), name='teacher-info'),
    #^======================Centers======================^#
    path('centers/list/', views.CenterListView.as_view(), name='center-info'),
    path('timing-center/<int:center_id>/', views.TimingCenterListView.as_view(), name='TimingCenterListView'),
    #^======================Books & Distributor ======================^#
    path('books/list/', views.BookListView.as_view(), name='book-info'),
    path('distributors/list/', views.DistributorListView.as_view(), name='distributor-info'),
    path('distributor/books/list/', views.DistributorBooksList.as_view(), name='distributor-info'),
]
