from django.contrib import admin

from exam.models import StudentBank, VideoQuiz,Answer, EssaySubmission, Exam, ExamQuestion, Question, QuestionCategory, Result, ResultTrial, Submission, VideoQuizResult

# Register your models here.

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id','text', 'points', 'difficulty', 'category', 'video', 'unit', 'is_active', 'created')
    list_editable = ('is_active',)

admin.site.register(Exam)
admin.site.register(QuestionCategory)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
# admin.site.register(Submission)
# admin.site.register(EssaySubmission)
# admin.site.register(Result)
# admin.site.register(ResultTrial)
admin.site.register(VideoQuiz)
admin.site.register(VideoQuizResult)
# admin.site.register(ExamQuestion)

@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'question', 'is_active', 'order', 'created')
    list_editable = ('is_active', 'order')
    list_filter = ('exam', 'is_active', 'order')
    search_fields = ('exam__title', 'question__text')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Submission model.
    Allows for easy viewing and filtering of student submissions.
    """
    list_display = (
        'id', # Always good to have the ID
        'student',
        'exam',
        'question',
        'selected_answer',
        'is_correct',
        'is_solved',
        'result_trial',
    )
    list_filter = (
        'exam', # Filter by the associated exam
        'student', # Filter by the submitting student
        'is_correct', # Filter by whether the answer was correct
        'is_solved', # Filter by whether the question was solved
        'result_trial', # Filter by the associated result trial
    )
    search_fields = (
        'student__user__username', # Assuming Student model has a user field with username
        'student__full_name', # If Student has a full_name field
        'exam__title', # Search by exam title
        'question__text', # Search by question text
    )
    raw_id_fields = ('student', 'exam', 'question', 'selected_answer', 'result_trial') # Use raw_id_fields for FKs to improve performance for many records

@admin.register(EssaySubmission)
class EssaySubmissionAdmin(admin.ModelAdmin):
    """
    Admin configuration for the EssaySubmission model.
    Provides tools for managing and scoring essay type submissions.
    """
    list_display = (
        'id', # Always good to have the ID
        'student',
        'exam',
        'question',
        'score',
        'is_scored',
        'created',
        'result_trial',
        'answer_file', # Display if a file was uploaded
    )
    list_filter = (
        'exam', # Filter by the associated exam
        'student', # Filter by the submitting student
        'is_scored', # Filter by whether the essay has been scored
        'result_trial', # Filter by the associated result trial
        'created', # Filter by creation date
    )
    search_fields = (
        'student__user__username', # Assuming Student model has a user field with username
        'student__full_name', # If Student has a full_name field
        'exam__title', # Search by exam title
        'question__text', # Search by question text
        'answer_text', # Search within the essay answer text
    )
    raw_id_fields = ('student', 'exam', 'question', 'result_trial') # Use raw_id_fields for FKs
    readonly_fields = ('created',) # Make 'created' field read-only in the admin

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Result model.
    Manages overall exam results for students.
    """
    list_display = (
        'id',
        'student',
        'exam',
        'trial',
        'added',
        'exam_model',
        'is_succeeded',         # Property from the Result model
        'is_trials_finished',   # Property from the Result model
        'has_unsubmitted_trial',# Property from the Result model
    )
    list_filter = (
        'exam',
        'student',
        'trial',
        'exam_model',
        'added', # Filter by date added
    )
    search_fields = (
        'student__user__username',
        'student__full_name',
        'exam__title',
    )
    raw_id_fields = ('student', 'exam', 'exam_model')
    readonly_fields = ('added',) # 'added' is auto_now_add, so it should be read-only


@admin.register(ResultTrial)
class ResultTrialAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ResultTrial model.
    Manages individual trial attempts within a student's exam result.
    """
    list_display = (
        'id',
        'result',
        'trial',
        'score',
        'exam_score',
        'exam_model',
        'student_started_exam_at',
        'student_submitted_exam_at',
        'submit_type',
    )
    list_filter = (
        'result__exam', # Filter by the exam associated with the parent result
        'result__student', # Filter by the student associated with the parent result
        'trial',
        'submit_type',
        'exam_model',
        'student_started_exam_at', # Filter by start date
        'student_submitted_exam_at', # Filter by submission date
    )
    search_fields = (
        'result__student__user__username',
        'result__student__full_name',
        'result__exam__title',
    )
    raw_id_fields = ('result', 'exam_model')
    readonly_fields = (
        'student_started_exam_at',
        'score', # Score is likely calculated, so make it read-only
        'exam_score', # Exam score is likely calculated, so make it read-only
    )


@admin.register(StudentBank)
class StudentBankAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'add_reason', 'is_solved_now', 'created')
    list_filter = ('add_reason', 'is_solved_now', 'created')
    search_fields = ('student__username', 'question__text')  # adjust field names if different
    ordering = ('-created',)

