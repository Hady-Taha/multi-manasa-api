from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Authentication -> ]============================== > ^#
    path("sign-in/", views.TeacherSignInView.as_view(), name="student_sign_in"),
    path("sign-up/", views.TeacherSignUpView.as_view(), name="student_sign_up"),
    #* < ==============================[ <- Profile -> ]============================== > ^#
    path("profile/", views.TeacherProfileView.as_view(), name="student_profile"),
    path("course-category/list/simple/", views.TeacherCourseCategoryView.as_view(), name="student_course_category"),
    #* < ==============================[ <- Course -> ]============================== > ^#
    
    #course
    path('course/list/', views.TeacherListCourseView.as_view(), name='teacher-course-list'),
    path('course/list/simple/', views.TeacherListCourseSimpleView.as_view(), name='teacher-course-simple-list'),
    path('course/create/', views.TeacherCreateCourseView.as_view(), name='teacher-create-course'),
    path('course/update/<int:id>/', views.TeacherUpdateCourseView.as_view(), name='teacher-update-course'),
    path('course/details/<int:id>/', views.TeacherDetailCourseView.as_view(), name='teacher-detail-course'),
    path('course/delete/<int:id>/', views.TeacherDeleteCourseView.as_view(), name='teacher-delete-course'),
    
    #unit
    path('course/unit/list/<int:course_id>/', views.TeacherListUnitView.as_view(), name='teacher-unit-list'),
    path('course/unit/create/<int:course_id>/', views.TeacherCreateUnitView.as_view(), name='teacher-create-unit'),
    path('course/unit/update/<int:id>/', views.TeacherUpdateUnitView.as_view(), name='teacher-update-unit'),
    path('course/unit/delete/<int:id>/', views.TeacherDeleteUnitView.as_view(), name='teacher-delete-unit'),
    path('course/unit/list/simple/<int:course_id>/', views.TeacherUnitListSimple.as_view(), name='extra-unit-list'),
    
    #video
    path('unit/video/list/<int:unit_id>/', views.TeacherListVideoView.as_view(), name='teacher-video-list'),
    path('unit/video/create/<int:unit_id>/', views.TeacherCreateVideoView.as_view(), name='teacher-create-video'),
    path('unit/video/update/<int:id>/', views.TeacherUpdateVideoView.as_view(), name='teacher-update-video'),
    path('unit/video/delete/<int:id>/', views.TeacherDeleteVideoView.as_view(), name='teacher-delete-video'),
    
    #Video File
    path('video/file/list/<int:video_id>/', views.TeacherVideoFileListView.as_view(), name='video-file-list'),
    path('video/file/create/<int:video_id>/', views.TeacherVideoFileCreateView.as_view(), name='video-file-create'),
    path('video/file/delete/<int:file_id>/', views.TeacherVideoFileDeleteView.as_view(), name='video-file-delete'),
    
    #File
    path('unit/file/list/<int:unit_id>/', views.TeacherListFileView.as_view(), name='teacher-file-list'),
    path('unit/file/create/<int:unit_id>/', views.TeacherCreateFileView.as_view(), name='teacher-create-file'),
    path('unit/file/update/<int:id>/', views.TeacherUpdateFileView.as_view(), name='teacher-update-file'),
    path('unit/file/delete/<int:id>/', views.TeacherDeleteFileView.as_view(), name='teacher-delete-file'),
    
    #* < ==============================[ <- Unit Content -> ]============================== > ^#
    path('unit/content/<int:unit_id>/', views.UnitContentView.as_view(), name='teacher-unit-content'),
    #* < ==============================[ <- Invoice -> ]============================== > ^#
    path('invoice/list/', views.TeacherInvoiceList.as_view(), name='teacher-invoice-list'),

    #* < ==============================[ <- Subscription -> ]============================== > ^#
    path('subscription/list/', views.TeacherCourseSubscriptionList.as_view(), name='course_subscription_list'),
    path('subscription/cancel/', views.TeacherCancelSubscription.as_view(), name='cancel-subscription'),
    path("subscription/renew/", views.TeacherRenewSubscription.as_view(), name="renew-subscription"),

    
    #* < ==============================[ <- Student -> ]============================== > ^#
    path('student/list/', views.TeacherListStudentView.as_view(), name='teacher-student-list'),
    path('student/center/sign-up/code/', views.TeacherCenterStudentSignUpView.as_view(), name='teacher-center-student-sign-up'),
]