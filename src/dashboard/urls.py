from django.urls import path
from . import views
urlpatterns = [

    #* < ==============================[ <- Student -> ]============================== > ^#
    path("student/list/", views.StudentsListView.as_view(), name="student_list"),
    path("student/update/<int:id>/", views.StudentUpdateView.as_view(), name="StudentUpdateView"),
    path("student/details/<int:id>/", views.StudentDetailView.as_view(), name="StudentDetailView"),
    path("student/delete/<str:username>/", views.UserDeleteView.as_view(), name="UserDeleteView"),
    path("student/rest-password/<str:username>/", views.UserRestPasswordView.as_view(), name="UserRestPasswordView"),
    path("student/change-center-status/", views.ChangeStudentCenterStatus.as_view(), name="ChangeStudentCenterStatus"),
    path("student/sign-code/", views.StudentSignCodeView.as_view(), name="ChangeStudentByCode"),
    path("student/points/list/", views.StudentPointListView.as_view(), name="ChangeStudentByCode"),
    path("student/sessions/list/", views.StudentLoginSessionView.as_view(), name="StudentLoginSessionView"),
    path("student/block/create/", views.StudentBlockCreateView.as_view(), name="StudentBlock"),
    path("student/block/list/", views.StudentBlockListView.as_view(), name="StudentBlock"),
    path("student/device/list/",views.StudentDeviceListView.as_view(),name='StudentBlockListView'),
    path('student/device/delete/<int:id>/', views.StudentDeviceDeleteView.as_view(),name='StudentDeviceDeleteView'),

    #* < ==============================[ <- Staff -> ]============================== > ^#
    path("staff/list/", views.StaffListView.as_view(), name="StaffListView"),
    path("staff/create/", views.CreateStaffView.as_view(), name="CreateStaffView"),
    path("staff/profile/",views.StaffProfileView.as_view(),name="staff_profile"),
    path("staff/sign-in/",views.StaffSignInView.as_view(),name="StaffSignInView"),

    #* < ==============================[ <- Permissions -> ]============================== > *#
    path("permission/group/list/", views.PermissionGroupListView.as_view(), name="PermissionGroupListView"),
    path("permission/group/assign/", views.AssignGroupToUserView.as_view(), name="PermissionGroupListView"),

    #* < ==============================[ <- CourseCategory -> ]============================== > ^#
    path('course/category/list/', views.CourseCategoryListView.as_view(), name='course-category-list'),
    path('course/category/list/simple/', views.CourseCategoryListSimpleView.as_view(), name='course-category-list-simple'),
    path('course/category/create/', views.CourseCategoryCreateView.as_view(), name='course-category-create'),
    path('course/category/update/<int:id>/', views.CourseCategoryUpdateView.as_view(), name='course-category-update'),
    path('course/category/delete/<int:id>/', views.CourseCategoryDeleteView.as_view(), name='course-category-delete'),
    
    #* < ==============================[ <- Teacher -> ]============================== > ^#
    path('teacher/list/', views.TeacherListView.as_view(), name="TeacherListView"),
    path("teacher/list/simple/", views.TeacherSimpleListView.as_view(), name="student_course_category"),
    path("teacher/rest-password/<str:username>/",views.UserRestPasswordView.as_view(), name="UserRestPasswordView"),
    path('teacher/create/',views.TeacherCreateView.as_view(),name="Create-Teacher"),
    path('teacher/update/<int:id>/', views.TeacherUpdateView.as_view(), name="Update-Teacher"),
    path('teacher/delete/<int:id>/', views.TeacherDeleteView.as_view(), name="Delete-Teacher"),
    
    #* < ==============================[ <- Course -> ]============================== > ^#
    path('course/list/', views.CourseListView.as_view(), name='course-list'),
    path('course/details/<int:id>/', views.CourseDetailView.as_view(), name='course-details'),
    path('course/create/', views.CourseCreateView.as_view(), name='course-create'),
    path('course/update/<int:id>/', views.CourseUpdateView.as_view(), name='update-course'),
    path('course/delete/<int:id>/', views.CourseDeleteView.as_view(), name='delete-course'),
    path('course/list/simple/', views.CourseListSimple.as_view(), name='course-list-simple'),

    #* < ==============================[ <- Unit -> ]============================== > *#
    path('course/unit/list/<int:course_id>/', views.UnitListView.as_view(), name='unit-list'),
    path('course/unit/create/<int:course_id>/', views.UnitCreateView.as_view(), name='unit-create'),
    path('course/unit/update/<int:unit_id>/', views.UnitUpdateView.as_view(), name='unit-update'),
    path('course/unit/delete/<int:unit_id>/', views.UnitDeleteView.as_view(), name='unit-delete'),
    path('course/unit/content/<int:unit_id>/', views.UnitContentView.as_view(), name='unit-create'),
    path('course/unit/resort/', views.UnitResortView.as_view(), name='course-units-resort'),
    path('course/unit/resort/subunit/', views.SubunitResortView.as_view(), name='course-units-resort'),
    path('course/unit/copy/', views.UnitCopyView.as_view(), name='copy-unit'),
    path('course/unit/list/simple/<int:course_id>/', views.UnitListSimple.as_view(), name='extra-unit-list'),

    #* < ==============================[ <- Content -> ]============================== > ^#
    #Video
    path('unit/video/list/<int:unit_id>/', views.VideoListView.as_view(), name='video-list'),
    path('unit/video/create/<int:unit_id>/', views.VideoCreateView.as_view(), name='video-create'),
    path('video/update/<int:video_id>/', views.VideoUpdateView.as_view(), name='video-update'),
    path('video/delete/<int:video_id>/', views.VideoDeleteView.as_view(), name='video-delete'),
    path('video/list/simple/<int:unit_id>/', views.VideoSimpleList.as_view(), name='video-delete'),

    #Video File
    path('video/file/list/<int:video_id>/', views.VideoFileListView.as_view(), name='video-file-list'),
    path('video/file/create/<int:video_id>/', views.VideoFileCreateView.as_view(), name='video-file-create'),
    path('video/file/delete/<int:file_id>/', views.VideoFileDeleteView.as_view(), name='video-file-delete'),

    #File
    path('unit/file/list/<int:unit_id>/', views.FileListView.as_view(), name='file-list'),
    path('unit/file/create/<int:unit_id>/', views.FileCreateView.as_view(), name='file-create'),
    path('file/delete/<int:file_id>/', views.FileDeleteView.as_view(), name='file-delete'),
    
    #Access Content
    path('content-details/<str:content_type>/<int:content_id>/', views.ContentDetailsView.as_view(), name='content-details'),

    #Sort Content
    path('content/resort/', views.ContentResortView.as_view(), name='unit-content-resort'),

    #* < ==============================[ <- CODES -> ]============================== > *#
    #Course
    path('codes/course/generate/', views.CodeCourseGenerate.as_view(), name='code-generate-course'),
    path('codes/course/list/', views.CodeCourseListView.as_view(), name='course-code-list'),

    #Video
    path('codes/video/generate/', views.CodeVideoGenerate.as_view(), name='code-generate-video'),
    path('codes/video/list/', views.CodeVideoListView.as_view(), name='course-code-list'),

    #Student
    path('codes/student/generate/', views.GenerateTeacherCenterStudentCodes.as_view(), name='generate-student-codes'),
    path('codes/student/list/', views.StudentTeacherCenterCodesListView.as_view(), name='list-student-codes'),

    
    #* < ==============================[ <- Invoice -> ]============================== > ^#
    path('invoice/list/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoice/update/<int:id>/', views.UpdateInvoicePayStatusView.as_view(), name='invoice-update'),
    path('invoice/create/', views.CreateInvoiceManually.as_view(), name='create-invoice-manually'),
    
    #PromoCode
    path('invoice/promo-code/list/', views.ListPromoCode.as_view(), name='promo-code-list'),
    path('invoice/promo-code/create/', views.CreatePromoCode.as_view(), name='create-promo-code'),
    path('invoice/promo-code/update/<int:id>/', views.UpdatePromoCode.as_view(), name='update-promo-code'),


    #* < ==============================[ <- Subscription -> ]============================== > ^#
    path('subscription/list/', views.CourseSubscriptionList.as_view(), name='course_subscription_list'),
    path('subscription/cancel/', views.CancelSubscription.as_view(), name='cancel-subscription'),
    path('subscription/cancel/bulk/', views.CancelSubscriptionBulk.as_view(), name='cancel-subscription-bulk'),
    path('subscription/start/bulk/', views.SubscriptionStartBulk.as_view(), name='cancel-subscription-bulk'),
    path("subscription/renew/", views.RenewSubscription.as_view(), name="RenewSubscription"),


    #* < ==============================[ <- View -> ]============================== > ^#
    path('views/video/list/', views.VideoViewList.as_view(), name='ViewList'),
    path('views/video/update-counter/<int:view_id>/', views.UpdateStudentView.as_view(), name='UpdateStudentView'),
    path('views/video/not-viewed-video/<int:video_id>/', views.StudentsNotViewedVideo.as_view(), name='StudentsNotViewedVideo'),
    path('views/video/sessions/list/',views.VideoViewSessionsList.as_view(),name="VideoViewSessionsList"),


    #* < ==============================[ <- Info -> ]============================== > ^#
    path("info/teacher-info/list/", views.TeacherInfoListView.as_view(), name='teacher-info-list'),
    # Center
    path("info/center/list/", views.CenterListView.as_view(), name="center-list"),
    path("info/center/create/", views.CenterCreateView.as_view(), name="center-create"),
    path("info/center/update/<int:id>/", views.CenterUpdateView.as_view(), name="center-update"),
    path("info/center/delete/<int:id>/", views.CenterDeleteView.as_view(), name='center-delete'),
    # Timing
    path("info/timing-center/list/<int:center_id>/", views.TimingCenterListView.as_view(), name="center-list"),
    path("info/timing-center/create/",views.TimingCenterCreateView.as_view(), name="center-create"),
    path("info/timing-center/update/<int:id>/", views.TimingCenterUpdateView.as_view(), name="center-update"),
    path("info/timing-center/delete/<int:id>/", views.TimingCenterDeleteView.as_view(), name="center-delete"),
    # Books
    path("info/book/list/", views.BookListView.as_view(), name="book-list"),
    path("info/book/create/", views.BookCreateView.as_view(), name="book-create"),
    path("info/book/update/<int:id>/", views.BookUpdateView.as_view(), name="book-update"),
    path("info/book/delete/<int:id>/", views.BookDeleteView.as_view(), name="book-delete"),
    # Distributor
    path("info/distributor/list/", views.DistributorListView.as_view(), name="distributor-list"),
    path("info/distributor/create/", views.DistributorCreateView.as_view(), name="distributor-create"),
    path("info/distributor/update/<int:id>/", views.DistributorUpdateView.as_view(), name="distributor-update"),
    path("info/distributor/delete/<int:id>/", views.DistributorDeleteView.as_view(), name="distributor-delete"),
    # Distributor Books
    path("info/distributor-book/list-books/<int:distributor_id>/", views.DistributorBookListView.as_view(), name="distributor-book-list"),
    path("info/distributor-book/add-books/<int:distributor_id>/", views.DistributorBookAddView.as_view(), name="distributor-book-add"),
    path("info/distributor-book/update-books/<int:distributor_id>/", views.DistributorBookAvailabilityUpdateView.as_view(), name="distributor-book-update"),
    path("info/distributor-book/delete-books/<int:distributor_id>/", views.DistributorBookDeleteView.as_view(), name="distributor-book-delete"),

    #* < ==============================[ <- Logs -> ]============================== > ^#
    path('logs/', views.RequestLogListView.as_view(), name='request-logs-list'),
    path('logs/delete/', views.RequestLogDeleteView.as_view(), name='request-logs-delete'),


    #* < ==============================[ <- CenterApp -> ]============================== > ^#
    path('center-app/exam-center/list/', views.ExamCenterList.as_view(), name='exam-center-list'),
    path('center-app/exam/center/result/list/', views.ResultExamCenterList.as_view(), name='result-exam-center-list'),
    
    #* < ==============================[ <- Analysis -> ]============================== > ^#
    path('analysis/invoice/', views.InvoiceChartData.as_view(), name='analysis-invoice-list'),
    
    #* < ==============================[ <- Notification -> ]============================== > ^#
    path('notification/create/', views.NotificationCreateView.as_view(), name='notification-create'),
    
    #^ < ==============================[ <- Exam -> ]============================== > ^#
    #^ QuestionCategory
    path('question-categories/', views.QuestionCategoryListCreateView.as_view(), name='question-category-list-create'),
    path('question-categories/<int:pk>/', views.QuestionCategoryRetrieveUpdateDestroyView.as_view(), name='question-category-detail'),
    #^ Question
    path('questions/', views.QuestionListCreateView.as_view(), name='question-list-create'),
    path('questions/<int:pk>/', views.QuestionRetrieveUpdateDestroyView.as_view(), name='question-detail'),
    path('questions/bulk/', views.BulkQuestionCreateView.as_view(), name='question-bulk-create'),
    #^ Answres
    path('answers/', views.AnswerListCreateView.as_view(), name='answer-list-create'),
    path('answers/<int:pk>/', views.AnswerRetrieveUpdateDestroyView.as_view(), name='answer-detail'),
    #^ Available Questions counts with different types and filters
    path('questions/count/', views.QuestionCountView.as_view(), name='question-count'),
    #^ Exams
    path('exams/', views.ExamListCreateView.as_view(), name='exam-list-create'),
    path('exams/<int:pk>/', views.ExamDetailView.as_view(), name='exam-detail'),
    #^ Exam Questions
    path('exams/<int:exam_id>/questions/', views.GetExamQuestions.as_view(), name='get_exam_questions'),
    path('exams/<int:exam_id>/questions/<int:question_id>/', views.RemoveExamQuestion.as_view(), name='remove_exam_question'),
    path('exams/<int:exam_id>/add-bank-questions/', views.AddBankExamQuestionsView.as_view()),
    path('exams/<int:exam_id>/add-manual-questions/', views.AddManualExamQuestionsView.as_view()),
    # Random Bank (small bank for Random Exams)
    path('exams/<int:exam_id>/random-bank/', views.GetRandomExamBank.as_view(), name='get-random-exam-bank'),
    path('exams/<int:exam_id>/random-bank/add/', views.AddToRandomExamBank.as_view(), name='add-to-random-exam-bank'),
    #^ Exam Models
    path('exams/models/<int:exam_model_id>/questions/', views.GetExamModelQuestions.as_view(), name='get-exam-model-questions'),
    path('exams/models/<int:exam_model_id>/questions/<int:question_id>/', views.RemoveQuestionFromExamModel.as_view(), name='remove-question-from-exam-model'),
    #^ ExamModels
    path('exammodels/', views.ExamModelListCreateView.as_view(), name='exammodel-list-create'),
    path('exammodels/<int:pk>/', views.ExamModelRetrieveUpdateDestroyView.as_view(), name='exammodel-retrieve-update-destroy'),
    #^ Suggest questions for an exam model
    path('exams/<int:exam_id>/suggest-questions/', views.SuggestQuestionsForModel.as_view(), name='suggest-questions'),
    #^ Add questions to an existing exam model
    path('exams/<int:exam_id>/exam-model/<int:exam_model_id>/add-questions/', views.AddQuestionsToModel.as_view(), name='add-questions-to-model'),
    #^ Essay Submissions
    path('exams/essay-submissions/', views.EssaySubmissionListView.as_view(), name='essay-submissions-list'),
    path('exams/essay-submissions/<int:submission_id>/score/', views.ScoreEssayQuestion.as_view(), name='score-essay-question'),
    #^ Results
    path('exams/exam-results/', views.ResultListView.as_view(), name='exams-results'),
    path('exams/exam-results/<int:result_id>/', views.ExamResultDetailView.as_view(), name='get-result-details'),
    path('exams/exam-results/<int:result_id>/<int:result_trial_id>/', views.ExamResultDetailForTrialView.as_view(), name='get-result-details-for-trial'),
    path('exams/reduce_trial/<int:result_id>/', views.ReduceResultTrialView.as_view(), name='update-result'),
    #^ Trial Results
    path('exams/result-trials/<int:result_id>/', views.ResultTrialsView.as_view(), name='result-trials-list'),

    path('exams/<int:exam_id>/took_exam/', views.StudentsTookExamAPIView.as_view(), name='students-took-exam'),
    path('exams/<int:exam_id>/did_not_take_exam/', views.StudentsDidNotTakeExamAPIView.as_view(), name='students-did-not-take-exam'),
    path('exams/<int:student_id>/exams_taken/', views.ExamsTakenByStudentAPIView.as_view(), name='exams-taken-by-student'),
    path('exams/<int:student_id>/exams_not_taken/', views.ExamsNotTakenByStudentAPIView.as_view(), name='exams-not-taken-by-student'),
    
    path('exams/<int:exam_id>/copy/', views.CopyExamView.as_view(), name='copy-exam'),
    path('exams/exam-questions/reorder/', views.ExamQuestionReorderAPIView.as_view(), name='exam_question_reorder'),
    #^ < ==============================[ <- Student Temp Exams -> ]============================== > ^#
    path('temp-exam-allowed-times/', views.CreateOrUpdateTempExamAllowedTimes.as_view(), name='temp-exam-allowed-times'),
    #^ < ==============================[ <- video quiz -> ]============================== > ^#
    path('video-quizzes/', views.VideoQuizListCreateAPIView.as_view(), name='videoquiz-list-create'),
    path('video-quizzes/<int:pk>/', views.VideoQuizRetrieveUpdateDestroyAPIView.as_view(), name='videoquiz-detail'),\


]
