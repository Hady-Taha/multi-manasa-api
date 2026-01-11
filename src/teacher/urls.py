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
    path('video/list/', views.TeacherAllVideos.as_view(), name='teacher-all-videos'),
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
    path("student/details/<int:student_id>/",views.TeacherStudentDetailView.as_view(),name="teacher-student-detail",),
    path("student/sessions/list/", views.TeacherStudentLoginSessionView.as_view(), name="StudentLoginSessionView"),
    #* < ==============================[ <- View -> ]============================== > ^#
    path('views/video/list/', views.TeacherVideoViewList.as_view(), name='teacher-video-view-list'),
    path('views/video/sessions/list/', views.TeacherVideoViewSessionsList.as_view(), name='teacher-video-view-sessions-list'),
    #^ < ==============================[ <- Exam -> ]============================== > ^#
    #^ QuestionCategory
    path('question-categories/', views.TeacherQuestionCategoryListCreateView.as_view(), name='question-category-list-create'),
    path('question-categories/<int:pk>/', views.TeacherQuestionCategoryRetrieveUpdateDestroyView.as_view(), name='question-category-detail'),
    #^ Question
    path('questions/', views.TeacherQuestionListCreateView.as_view(), name='question-list-create'),
    path('questions/<int:pk>/', views.TeacherQuestionRetrieveUpdateDestroyView.as_view(), name='question-detail'),
    path('questions/bulk/', views.TeacherBulkQuestionCreateView.as_view(), name='question-bulk-create'),
    #^ Answres
    path('answers/', views.TeacherAnswerListCreateView.as_view(), name='answer-list-create'),
    path('answers/<int:pk>/', views.TeacherAnswerRetrieveUpdateDestroyView.as_view(), name='answer-detail'),
    #^ Available Questions counts with different types and filters
    path('questions/count/', views.TeacherQuestionCountView.as_view(), name='question-count'),
    #^ Exams
    path('exams/', views.TeacherExamListCreateView.as_view(), name='exam-list-create'),
    path('exams/<int:pk>/', views.TeacherExamDetailView.as_view(), name='exam-detail'),
    #^ Exam Questions
    path('exams/<int:exam_id>/questions/', views.TeacherGetExamQuestions.as_view(), name='get_exam_questions'),
    path('exams/<int:exam_id>/questions/<int:question_id>/', views.TeacherRemoveExamQuestion.as_view(), name='remove_exam_question'),
    path('exams/<int:exam_id>/add-bank-questions/', views.TeacherAddBankExamQuestionsView.as_view()),
    path('exams/<int:exam_id>/add-manual-questions/', views.TeacherAddManualExamQuestionsView.as_view()),
    # Random Bank (small bank for Random Exams)
    path('exams/<int:exam_id>/random-bank/', views.TeacherGetRandomExamBank.as_view(), name='get-random-exam-bank'),
    path('exams/<int:exam_id>/random-bank/add/', views.TeacherAddToRandomExamBank.as_view(), name='add-to-random-exam-bank'),
    #^ Exam Models
    path('exams/models/<int:exam_model_id>/questions/', views.TeacherGetExamModelQuestions.as_view(), name='get-exam-model-questions'),
    path('exams/models/<int:exam_model_id>/questions/<int:question_id>/', views.TeacherRemoveQuestionFromExamModel.as_view(), name='remove-question-from-exam-model'),
    #^ ExamModels
    path('exammodels/', views.TeacherExamModelListCreateView.as_view(), name='exammodel-list-create'),
    path('exammodels/<int:pk>/', views.TeacherExamModelRetrieveUpdateDestroyView.as_view(), name='exammodel-retrieve-update-destroy'),
    #^ Suggest questions for an exam model
    path('exams/<int:exam_id>/suggest-questions/', views.TeacherSuggestQuestionsForModel.as_view(), name='suggest-questions'),
    #^ Add questions to an existing exam model
    path('exams/<int:exam_id>/exam-model/<int:exam_model_id>/add-questions/', views.TeacherAddQuestionsToModel.as_view(), name='add-questions-to-model'),
    #^ Essay Submissions
    path('exams/essay-submissions/', views.TeacherEssaySubmissionListView.as_view(), name='essay-submissions-list'),
    path('exams/essay-submissions/<int:submission_id>/score/', views.TeacherScoreEssayQuestion.as_view(), name='score-essay-question'),
    #^ Results
    path('exams/exam-results/', views.TeacherResultListView.as_view(), name='exams-results'),
    path('exams/exam-results/<int:result_id>/', views.TeacherExamResultDetailView.as_view(), name='get-result-details'),
    path('exams/exam-results/<int:result_id>/<int:result_trial_id>/', views.TeacherExamResultDetailForTrialView.as_view(), name='get-result-details-for-trial'),
    path('exams/reduce_trial/<int:result_id>/', views.TeacherReduceResultTrialView.as_view(), name='update-result'),
    #^ Trial Results
    path('exams/result-trials/<int:result_id>/', views.TeacherResultTrialsView.as_view(), name='result-trials-list'),

    path('exams/<int:exam_id>/took_exam/', views.TeacherStudentsTookExamAPIView.as_view(), name='students-took-exam'),
    path('exams/<int:exam_id>/did_not_take_exam/', views.TeacherStudentsDidNotTakeExamAPIView.as_view(), name='students-did-not-take-exam'),
    path('exams/<int:student_id>/exams_taken/', views.TeacherExamsTakenByStudentAPIView.as_view(), name='exams-taken-by-student'),
    path('exams/<int:student_id>/exams_not_taken/', views.TeacherExamsNotTakenByStudentAPIView.as_view(), name='exams-not-taken-by-student'),
    
    path('exams/<int:exam_id>/copy/', views.TeacherCopyExamView.as_view(), name='copy-exam'),
    path('exams/exam-questions/reorder/', views.TeacherExamQuestionReorderAPIView.as_view(), name='exam_question_reorder'),
    
    #^ < ==============================[ <- video quiz -> ]============================== > ^#
    path('video-quizzes/', views.TeacherVideoQuizListCreateAPIView.as_view(), name='videoquiz-list-create'),
    path('video-quizzes/<int:pk>/', views.TeacherVideoQuizRetrieveUpdateDestroyAPIView.as_view(), name='videoquiz-detail'),

]