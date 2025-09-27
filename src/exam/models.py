from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum
from course.models import Course, Video, Unit
from student.models import Year,Student
from django.utils.timezone import now


# Choices
class RelatedToChoices(models.TextChoices):
    UNIT = 'UNIT', _('Unit')
    VIDEO = 'VIDEO', _('Video')

class DifficultyLevel(models.TextChoices):
    EASY = 'EASY', _('Easy')
    MEDIUM = 'MEDIUM', _('Medium')
    HARD = 'HARD', _('Hard')

class ExamType(models.TextChoices):
    RANDOM = 'RANDOM', _('Random')
    MANUAL = 'MANUAL', _('Manual')
    BANK = 'BANK', _('Pic From the Bank')

class QuestionType(models.TextChoices):
    MCQ = 'MCQ', _('Multiple Choice Question')
    ESSAY = 'ESSAY', _('Essay Question')

class Exam(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField(null=True, blank=True)
    related_to = models.CharField(max_length=10, choices=RelatedToChoices.choices)
    
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name='exams', null=True, blank=True
    )
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name='exams', null=True, blank=True
    )
    
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='exams', null=True, blank=True
    )
    
    number_of_questions = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(help_text="Time limit in minutes")
    score = models.FloatField(default=0.0)
    passing_percent = models.PositiveIntegerField(default=50)
    created = models.DateTimeField(auto_now_add=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    number_of_allowed_trials = models.PositiveIntegerField(default=1)
    
    type = models.CharField(
        max_length=10, choices=ExamType.choices, default=ExamType.MANUAL
    )
    
    easy_questions_count = models.PositiveIntegerField(default=0)
    medium_questions_count = models.PositiveIntegerField(default=0)
    hard_questions_count = models.PositiveIntegerField(default=0)
    show_answers_after_finish = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    allow_show_results_at = models.DateTimeField(default=timezone.now)
    allow_show_answers_at = models.DateTimeField(null=True, blank=True)
    is_depends = models.BooleanField(default=False)
    show_questions_in_random = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if self.easy_questions_count + self.medium_questions_count + self.hard_questions_count > self.number_of_questions:
            raise ValidationError(_("The total count of questions cannot exceed the number of questions."))
        if self.related_to == RelatedToChoices.UNIT and not self.unit:
            raise ValidationError(_("Unit is required when related to unit."))
        if self.related_to == RelatedToChoices.VIDEO and not self.video:
            raise ValidationError(_("video is required when related to video."))
        if self.unit and self.video:
            raise ValidationError(_("Cannot set both unit and video."))
        if self.type == ExamType.RANDOM:
            self.validate_random_exam()

    def validate_random_exam(self):
        if self.related_to == RelatedToChoices.VIDEO:
            related_queryset = Question.objects.filter(video=self.video)
        elif self.related_to == RelatedToChoices.UNIT:
            related_queryset = Question.objects.filter(unit=self.unit)
        else:
            raise ValidationError(_("Exam must be related to either a unit or a video."))

        easy_count = related_queryset.filter(difficulty=DifficultyLevel.EASY).count()
        medium_count = related_queryset.filter(difficulty=DifficultyLevel.MEDIUM).count()
        hard_count = related_queryset.filter(difficulty=DifficultyLevel.HARD).count()

        if self.easy_questions_count > easy_count:
            raise ValidationError(_("Not enough easy questions available for the selected count."))
        if self.medium_questions_count > medium_count:
            raise ValidationError(_("Not enough medium questions available for the selected count."))
        if self.hard_questions_count > hard_count:
            raise ValidationError(_("Not enough hard questions available for the selected count."))

    def status(self):
        if self.start > timezone.now():
            return 'soon'
        if self.end < timezone.now():
            return 'finished'
        return 'active'

    def get_related_name(self) -> str:
        if self.related_to == "UNIT" and self.unit:
            return self.unit.name
        elif self.related_to == "video" and self.video:
            return self.video.name
        return ""

    def get_related_course(self):
        if self.unit:
            return self.unit.course.id
        elif self.video:
            return self.video.unit.course.id
        return None

    def get_related_year(self):
        if self.unit:
            return self.unit.course.year.id
        elif self.video:
            return self.video.unit.course.year.id
        return None

    def calculate_score(self):
        if self.type == ExamType.RANDOM:
            return 'not_calculatable'
        elif self.type in [ExamType.MANUAL, ExamType.BANK]:
            total_score = self.exam_questions.aggregate(total=Sum('question__points'))['total'] or 0
            return total_score
        else:
            return 0

    def calculate_number_of_questions(self):
        if self.type == ExamType.RANDOM:
            return 'not_calculatable'
        elif self.type in [ExamType.MANUAL, ExamType.BANK]:
            return self.exam_questions.count()
        else:
            return 0

    def save(self, *args, **kwargs):
        course = Course.objects.filter(id=self.get_related_course()).first()
        if course:
            self.course = course
        else:
            self.course = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['created']

class QuestionCategory(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, db_index=True, related_name='questioncategories'
    )

    def __str__(self):
        return self.title

class Question(models.Model):
    text = models.TextField()
    image = models.ImageField(upload_to='questions/', null=True, blank=True)
    points = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=6, choices=DifficultyLevel.choices, default=DifficultyLevel.EASY)
    category = models.ForeignKey(
        QuestionCategory, on_delete=models.CASCADE, null=True, blank=True, db_index=True, related_name='categoryquestions'
    )
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, null=True, blank=True, db_index=True, related_name='videoquestions'
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, null=True, blank=True, db_index=True, related_name='unitquestions'
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='questions', null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    question_type = models.CharField(max_length=5, choices=QuestionType.choices, default=QuestionType.MCQ)
    comment = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Automatically set the unit based on the video if not provided
        if self.video and not self.unit:
            self.unit = self.video.unit
        # Automatically set the course based on category, unit or video if not provided
        if not self.course:
            if self.category and self.category.course:
                self.course = self.category.course
            elif self.unit:
                self.course = self.unit.course
            elif self.video:
                self.course = self.video.unit.course
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id) + " | " + str(self.question_type) + " | " + self.text

class Answer(models.Model):
    text = models.TextField()
    image = models.ImageField(upload_to='answers/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q: {self.question.text} | A: {self.text} | Correct: {self.is_correct}"

class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='exam_questions')
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True , null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    class Meta:
        ordering = ['order', 'created']
    def __str__(self):
        return f"Exam: {self.exam.title} | Question: {self.question.text} | Active: {self.is_active}"

class RandomExamBank(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='random_exam_bank')
    questions = models.ManyToManyField(Question, related_name='random_exam_bank')

    def __str__(self):
        return f"Random Exam Bank for {self.exam.title}"

class ExamModel(models.Model):
    """Model to store different versions of a random exam"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_models')
    title = models.CharField(max_length=120)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.exam.title} - Model: {self.title}"

class ExamModelQuestion(models.Model):
    """Questions assigned to a specific exam model"""
    exam_model = models.ForeignKey(ExamModel, on_delete=models.CASCADE, related_name='model_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('exam_model', 'question')

class Submission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    is_solved = models.BooleanField(default=True)
    result_trial = models.ForeignKey('ResultTrial', on_delete=models.SET_NULL, related_name='submissions', null=True, blank=True)

    class Meta:
        indexes = [
            # For efficient lookups by student and exam combination
            models.Index(fields=['student', 'exam']),
            # For result trial related queries
            models.Index(fields=['result_trial', 'is_correct']),
            # For question performance analysis
            models.Index(fields=['question', 'is_correct']),
            # For student performance tracking
            models.Index(fields=['student', 'is_correct', 'is_solved']),
        ]
        # Ensure unique submission per student, exam, question, and result_trial
        unique_together = [['student', 'exam', 'question', 'result_trial']]

    def save(self, *args, **kwargs):
        # Automatically check if the answer is correct
        if self.selected_answer:
            self.is_correct = self.selected_answer.is_correct
        else:
            self.is_correct = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.result_trial} |{self.question.text} | Correct: {self.is_correct} | Solved: {self.is_solved}"


class EssaySubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE,related_name='essaysubmissions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    answer_file = models.FileField(upload_to='essay_submissions/', null=True, blank=True)  # New field
    score = models.FloatField(null=True, blank=True)
    is_scored = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    result_trial = models.ForeignKey('ResultTrial', on_delete=models.CASCADE, related_name='essay_submissions', null=True, blank=True)

    class Meta:
        # Ensure unique essay submission per student, exam, question, and result_trial
        unique_together = [['student', 'exam', 'question', 'result_trial']]

    def __str__(self):
        return f" {self.result_trial} | {self.question.text} | Score: {self.score}"



class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    trial = models.PositiveIntegerField(default=0)
    added = models.DateTimeField(auto_now_add=True)
    exam_model = models.ForeignKey(
        ExamModel, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ('student', 'exam')  # One result per student-exam combination.

    @property
    def current_trial(self):
        """Fetch the ResultTrial for the current trial."""
        return self.trials.filter(trial=self.trial).first()

    @property
    def previous_trial(self):
        """Fetch the ResultTrial for the previous trial."""
        if self.trial > 1:
            return self.trials.filter(trial=self.trial - 1).first()
        return None

    @property
    def active_trial(self):
        """
        Fetch the active ResultTrial:
        - If the current trial is submitted, use it.
        - If the current trial is not submitted, use the previous trial (if it exists).
        """
        current_trial = self.current_trial
        if current_trial and current_trial.student_submitted_exam_at:
            return current_trial
        return self.previous_trial or current_trial

    @property
    def is_trials_finished(self):
        """Check if the student has finished his allowed trials."""
        # If all trials are submitted, check if we reached the limit
        if not self.trials.filter(student_submitted_exam_at__isnull=True).exists():
            return self.trial >= self.exam.number_of_allowed_trials
        # If there's an unsubmitted trial, trials are not finished
        return False

    @property
    def has_unsubmitted_trial(self):
        """Check if there's an unsubmitted trial."""
        return self.trials.filter(student_submitted_exam_at__isnull=True).exists()

    @property
    def is_succeeded(self):
        """Determine if the student passed the exam based on the active trial."""
        active_trial = self.active_trial
        if active_trial:
            return active_trial.score >= (self.exam.passing_percent / 100) * active_trial.exam_score
        return False

    def __str__(self):
        return f"{self.student.name} - {self.exam.title} | Trial: {self.trial}"


class ResultTrial(models.Model):
    # Define choices for the submit_type field
    SUBMIT_TYPE_CHOICES = [
        ('student_submit', 'Student Submit'),
        ('tab_closed', 'Tab Closed'),
        ('offline', 'Offline'),
        ('time_out', 'Time Out'),
    ]

    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='trials')
    trial = models.PositiveIntegerField()
    score = models.FloatField(default=0.0)
    exam_score = models.FloatField(default=0.0)  
    exam_model = models.ForeignKey(ExamModel, on_delete=models.SET_NULL, null=True, blank=True)
    student_started_exam_at = models.DateTimeField()
    student_submitted_exam_at = models.DateTimeField(null=True, blank=True)

    submit_type = models.CharField(
        max_length=20,
        choices=SUBMIT_TYPE_CHOICES,
        default='student_submit',
        null=True,  
        blank=True,
    )

    class Meta:
        unique_together = ('result', 'trial')  # Ensure one trial per result

    def __str__(self):
        return f"{self.id}"


class AddReasonChoices(models.TextChoices):
    INCORRECT = 'INCORRECT', _('Incorrect')
    UNSOLVED = 'UNSOLVED', _('Unsolved')
    PARTIAL_ESSAY = 'PARTIAL_ESSAY', _('Partial Essay Score')

class StudentBank(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_bank')
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='student_bank')
    add_reason = models.CharField(max_length=20, choices=AddReasonChoices.choices)
    is_solved_now = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'question')
        indexes = [
            models.Index(fields=['student', 'question']),
        ]

    def __str__(self):
        return f"{self.student.name} - Q: {self.question.id} - {self.add_reason}"

class TempExam(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='temp_exams')
    year = models.ForeignKey(Year, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, blank=True)
    number_of_questions = models.PositiveIntegerField()
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in minutes")
    created = models.DateTimeField(auto_now_add=True)
    result = models.FloatField(null=True, blank=True)
    selected_questions_type = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Temp Exam for {self.student.name} - {self.created}"


class TempExamAllowedTimes(models.Model):
    number_of_allowedtempexams_per_day = models.PositiveIntegerField(default=3)

    class Meta:
        # Ensure only one instance exists
        constraints = [
            models.CheckConstraint(
                check=models.Q(id=1),
                name='single_instance_constraint'
            )
        ]

    def save(self, *args, **kwargs):
        self.id = 1  # Enforce single instance
        super().save(*args, **kwargs)
    def __str__(self):
        return f"Allowed Temp Exams: {self.number_of_allowedtempexams_per_day} per day"


#ap:Video
#^ < ==============================[ <- Video Quiz -> ]============================== > ^#


class VideoQuiz(models.Model):
    # title = models.CharField(max_length=200)
    time = models.PositiveIntegerField(default=0, help_text="Time in seconds")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='video_quizzes',blank=True, null=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_quizzes')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)



    def save(self, *args, **kwargs):
        if self.video and not self.course:
            self.course = self.video.unit.course
        super().save(*args, **kwargs)




class VideoQuizResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    video_quiz = models.ForeignKey(VideoQuiz, on_delete=models.CASCADE, related_name='videoquizresults')
    exam_score = models.FloatField(default=0.0)
    student_score = models.FloatField(default=0.0)
    trial = models.PositiveIntegerField(default=1)
    added = models.DateTimeField(auto_now_add=True)
    def is_succeeded(self):
        """Determine if the student passed the video quiz based on the score."""
        return self.student_score >= (self.video_quiz.exam.passing_percent / 100) * self.exam_score

    class Meta:
        unique_together = ('student', 'video_quiz')