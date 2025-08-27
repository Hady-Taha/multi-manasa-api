from django.urls import path
from . import views

urlpatterns = [
    # Teacher
    path('teacher/list/', views.TeacherSimpleListView.as_view(), name='student-list'),
    # Student
    path('student/list/', views.TeacherStudentListView.as_view(), name='student-list'),
    # Course
    path('course/list/', views.CourseList.as_view(), name='course-list'),
    path('video/list/', views.VideoList.as_view(), name='video-list'),
    path('video-views/<int:video_id>/', views.VideoViewsList.as_view(), name='video-views-list'),
    path("course-views/<int:course_id>/", views.CourseViewsList.as_view(), name="course-views-list"),
    # Subscription
    path('subscribe-many-users/', views.SubscribeManyUsers.as_view(), name='subscribe-many-users'),
    
    path('exam-list/', views.ExamList.as_view(), name='exam-list'),
    path('exam-results/<int:exam_id>/', views.ExamResultList.as_view(), name='exam-results-list'),
    path('unsubscribe-many-users/', views.UnSubscribeManyUsers.as_view(), name='unsubscribe-many-users'),
    path('submit-result-exam/', views.SubmitResultCenterExam.as_view(), name='unsubscribe-many-users'),
    #* =================================Center================================= *#
    path('center-list/', views.CenterList.as_view(), name='center-list'),
    path('center-create/',views.CenterCreate.as_view(), name='center-create'),
    path('lecture-list/', views.LectureList.as_view(), name='lecture-list'),
    path('lecture-create/',views.LectureCreate.as_view(), name='lecture-create'),
    path('attendance-list/', views.AttendanceList.as_view(), name='attendance-list'),
    path('attendance-create/',views.AttendanceCreate.as_view(), name='attendance-create'),
]


