from django.urls import path
from . import views

app_name = 'exam'

urlpatterns = [
    path('<int:exam_id>/check_my_ability_to_start/', views.CheckExamStartAbility.as_view(), name='check-exam-start-ability'),
    path('<int:exam_id>/start/', views.StartExam.as_view(), name='start-exam'),
    path('<int:exam_id>/submit/', views.SubmitExam.as_view(), name='submit-exam'),
    path('exam-results/', views.StudentExamResultsView.as_view(), name='student-exam-results'),
    path('<int:exam_id>/result/', views.GetMyExamResult.as_view(), name='get-my-exam-result'),
    path('<int:exam_id>/result/<int:result_trial_id>/', views.GetMyExamResultForTrial.as_view(), name='get-my-exam-result-for-trial'),



    #^ ------- Vido Quiz ------- ^#
    path('<int:video_quiz_id>/video-quiz/', views.StartVideoQuiz.as_view(), name='start-video-quiz'),
    path('video-quiz-result/', views.UpdateVideoQuizResultView.as_view(), name='update-video-quiz-result'),
    path('video-quiz-results/', views.VideoQuizResultsListView.as_view(), name='video-quiz-results'),

    #^ ------- Student Temp Exams ------- ^#
    path('student-bank/', views.StudentBankListView.as_view(), name='student-bank-list'),
    path('create-temp-exam/', views.CreateTempExam.as_view(), name='create-temp-exam'),
    path('submit-temp-exam-results/', views.SubmitTempExamResults.as_view(), name='submit-temp-exam-results'),

]


