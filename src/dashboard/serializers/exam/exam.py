from rest_framework import serializers
from django.utils import timezone
from course.models import Course, Video, Unit
from course.serializers import CourseSerializer, VideoSerializer
from dashboard.serializers.student.student import StudentSerializer
from exam.models import Answer, DifficultyLevel, Exam, ExamModel, ExamModelQuestion, ExamQuestion, ExamType, Question, QuestionCategory, QuestionType, RandomExamBank, RelatedToChoices, Result, EssaySubmission, ResultTrial, Submission, TempExamAllowedTimes, VideoQuiz
from student.models import Student

class ExamSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    related_year = serializers.SerializerMethodField()
    related_course = serializers.SerializerMethodField()
    related_unit = serializers.SerializerMethodField()
    related_unit_name = serializers.SerializerMethodField()
    related_video_name = serializers.SerializerMethodField()
    related_course_name = serializers.SerializerMethodField()
    related_year_name = serializers.SerializerMethodField()
    calculated_score = serializers.SerializerMethodField()
    calculated_number_of_questions = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id", "title", "description",
            "related_to", "related_course", "related_course_name",
            "related_year", "related_year_name",
            "unit", "related_unit", "related_unit_name",
            "video", "related_video_name",
            "type", "number_of_questions", "time_limit",
            "number_of_allowed_trials", "easy_questions_count",
            "medium_questions_count", "hard_questions_count",
            "show_answers_after_finish", "order", "is_active",
            "start", "end", "allow_show_results_at","allow_show_answers_at", "created",
            "passing_percent", "status", "calculated_score","calculated_number_of_questions",
            'is_depends','show_questions_in_random',
        ]

        read_only_fields = ["id", "created", "status", "related_year", "related_course", "related_unit",
                            "related_unit_name", "related_video_name", "related_course_name","related_year_name","calculated_score","calculated_number_of_questions"]

    def get_status(self, obj):
        return obj.status()

    def get_related_year(self, obj):
        return obj.get_related_year()
    
    def get_related_year_name(self, obj):
        if obj.unit:
            return obj.unit.course.year.name
        elif obj.video:
            return obj.video.unit.course.year.name
        return None

    def get_related_course(self, obj):
        if obj.unit:
            return obj.unit.course.id
        elif obj.video:
            return obj.video.unit.course.id
        return None

    def get_related_unit(self, obj):
        if obj.unit:
            return obj.unit.id
        elif obj.video:
            return obj.video.unit.id
        return None

    def get_related_unit_name(self, obj):
        if obj.unit:
            return obj.unit.name
        return None

    def get_related_video_name(self, obj):
        if obj.video:
            return obj.video.name
        return None

    def get_related_course_name(self, obj):
        if obj.unit:
            return obj.unit.course.name
        elif obj.video:
            return obj.video.unit.course.name
        return None
    
    def get_calculated_score(self, obj):
        """
        Return the dynamically calculated score for the exam.
        """
        return obj.calculate_score()

    def get_calculated_number_of_questions(self, obj):
        return obj.calculate_number_of_questions()

    def validate(self, data):
        total_count = (
            data.get("easy_questions_count", 0) +
            data.get("medium_questions_count", 0) +
            data.get("hard_questions_count", 0)
        )
        if total_count > data.get("number_of_questions", 0):
            raise serializers.ValidationError("The total count of questions cannot exceed the number of questions.")

        related_to = data.get("related_to")
        unit = data.get("unit")
        video = data.get("video")

        if related_to == "UNIT" and not unit:
            raise serializers.ValidationError("Unit is required when related_to is 'UNIT'.")
        if related_to == "VIDEO" and not video:
            raise serializers.ValidationError("Video is required when related_to is 'VIDEO'.")
        if related_to == "UNIT" and video:
            raise serializers.ValidationError("it should be related to a unit but you selected a video.")
        if related_to == "VIDEO" and unit:
            raise serializers.ValidationError("it should be related to a video but you selected a unit.")
        if related_to != "UNIT" and related_to != "VIDEO":
            raise serializers.ValidationError("Exam must be related to either a unit or a video.")

        return data


class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ['id', 'title', 'course']

class AnswerSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Answer
        fields = ['id', 'text', 'image', 'is_correct', 'question']
        read_only_fields = ['id']
        extra_kwargs = {
            'question': {'required': False},
            'is_correct': {'required': False, 'default': False}
        }

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, required=False)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'text',
            'image',
            'points',
            'difficulty',
            'category',
            'video',
            'unit',
            'course',
            'is_active',
            'answers',
            'question_type',
            'comment',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        # Extract nested answers data
        answers_data = validated_data.pop('answers', [])
        
        # Create the Question object
        question = Question.objects.create(**validated_data)
        
        # Create Answer objects if provided
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        
        return question
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['answers'] = AnswerSerializer(instance.answers.all(), many=True).data
        return representation


class EssaySubmissionSerializer(serializers.ModelSerializer):
    answer_file_url = serializers.SerializerMethodField()

    class Meta:
        model = EssaySubmission
        fields = ['id', 'student', 'exam', 'question', 'answer_text', 'answer_file', 'answer_file_url', 'score', 'is_scored', 'created', 'result_trial']
        extra_kwargs = {
            'answer_file': {'write_only': True}  # Don't include in response, use answer_file_url instead
        }

    def get_answer_file_url(self, obj):
        if obj.answer_file:
            return self.context['request'].build_absolute_uri(obj.answer_file.url)
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['student'] = instance.student.name
        representation['exam'] = instance.exam.title
        representation['question'] = instance.question.text
        representation['question_comment'] = instance.question.comment
        if instance.question.image:
            representation['question_image'] = instance.question.image.url
        else:
            representation['question_image'] = None
        return representation

class RandomExamBankSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = RandomExamBank
        fields = ['exam', 'questions']

class ExamModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamModel
        fields = '__all__'

    def validate_exam(self, value):
        if value.type != ExamType.RANDOM:
            raise serializers.ValidationError("The exam type must be 'RANDOM'.")
        return value

class ResultSerializer(serializers.ModelSerializer):
    result_id = serializers.IntegerField(source='id')
    exam_id = serializers.IntegerField(source='exam.id', read_only=True)
    # exam_title = serializers.CharField(source='exam.title', read_only=True)
    # exam_description = serializers.CharField(source='exam.description', read_only=True)
    # exam_related_to = serializers.CharField(source='exam.related_to', read_only=True)
    # exam_unit = serializers.IntegerField(source='exam.unit.id', allow_null=True, read_only=True)
    # exam_video = serializers.IntegerField(source='exam.video.id', allow_null=True, read_only=True)
    # exam_course = serializers.SerializerMethodField()
    exam_score = serializers.SerializerMethodField()
    student_score = serializers.SerializerMethodField()
    number_of_allowed_trials = serializers.IntegerField(source='exam.number_of_allowed_trials', read_only=True)
    trials = serializers.IntegerField(source='trial')
    # trials_finished = serializers.BooleanField(source='is_trials_finished', read_only=True)
    # passing_percent = serializers.IntegerField(source='exam.passing_percent', read_only=True)
    # is_succeeded = serializers.SerializerMethodField()
    correct_questions_count = serializers.SerializerMethodField()
    incorrect_questions_count = serializers.SerializerMethodField()
    insolved_questions_count = serializers.SerializerMethodField()
    # number_of_questions = serializers.SerializerMethodField()
    allowed_to_show_result = serializers.SerializerMethodField()
    # added_at = serializers.DateTimeField(source='added', read_only=True)
    # start = serializers.DateTimeField(source='exam.start', read_only=True)
    # end = serializers.DateTimeField(source='exam.end', read_only=True)
    student_id = serializers.IntegerField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_phone = serializers.CharField(source='student.user.username', read_only=True)
    parent_phone = serializers.CharField(source='student.parent_phone', read_only=True)
    jwt_token = serializers.CharField(source='student.jwt_token', read_only=True)
    student_started_exam_at = serializers.SerializerMethodField()  # Fetch from ResultTrial
    student_submitted_exam_at = serializers.SerializerMethodField()  # Fetch from ResultTrial
    submit_type = serializers.SerializerMethodField()
    class Meta:
        model = Result
        fields = [
            'result_id',
            'exam_id',
            # 'exam_title',
            # 'exam_description',
            # 'exam_related_to',
            # 'exam_unit',
            # 'exam_video',
            # 'exam_course',
            'exam_score',
            'student_score',
            'trials',
            # 'trials_finished',
            'number_of_allowed_trials',
            # 'is_succeeded',
            'correct_questions_count',
            'incorrect_questions_count',
            'insolved_questions_count',
            # 'number_of_questions',
            'allowed_to_show_result',
            # 'passing_percent',
            # 'added_at',
            # 'start',
            # 'end',
            
            'student_id',
            'student_name',
            'student_phone',
            'parent_phone',
            'jwt_token',
            'student_started_exam_at',
            'student_submitted_exam_at',
            'submit_type',
        ]

    # def get_exam_course(self, obj):
    #     """Retrieve related course from the Exam model."""
    #     return obj.exam.get_related_course()

    def get_exam_score(self, obj):
        """Fetch the exam_score from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.exam_score
        return 0

    def get_student_score(self, obj):
        """Fetch the student's score from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.score
        return 0

    def get_correct_questions_count(self, obj):
        """Count correct submissions for the exam."""
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_correct=True,result_trial=obj.active_trial
        ).count()

    def get_incorrect_questions_count(self, obj):
        """Count incorrect submissions for the exam."""
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_correct=False,result_trial=obj.active_trial
        ).count()

    def get_insolved_questions_count(self, obj):
        """Count unsolved submissions for the exam."""
        return Submission.objects.filter(
            student=obj.student, exam=obj.exam, is_solved=False,result_trial=obj.active_trial
        ).count()

    # def get_number_of_questions(self, obj):
    #     """Get the total number of questions in the exam."""
    #     if obj.exam.type == ExamType.RANDOM and obj.exam_model:
    #         return ExamModelQuestion.objects.filter(exam_model=obj.exam_model).count()
    #     return Question.objects.filter(exam_questions__exam=obj.exam, is_active=True).count()

    def get_allowed_to_show_result(self, obj):
        """Check if the result can be shown."""
        return obj.exam.allow_show_results_at <= timezone.now()

    # def get_is_succeeded(self, obj):
    #     """Determine if the student passed the exam."""
    #     active_trial = obj.active_trial
    #     if active_trial:
    #         return active_trial.score >= (obj.exam.passing_percent / 100) * active_trial.exam_score
    #     return False

    def get_student_started_exam_at(self, obj):
        """Fetch the start time from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.student_started_exam_at
        return None

    def get_student_submitted_exam_at(self, obj):
        """Fetch the submission time from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.student_submitted_exam_at
        return None
    
    def get_submit_type(self, obj):
        """Fetch the submit_type from the active trial."""
        active_trial = obj.active_trial
        if active_trial:
            return active_trial.submit_type
        return None



class ResultTrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultTrial
        fields = [
            'id',
            'trial',
            'score',
            'submit_type',
            'student_started_exam_at',
            'student_submitted_exam_at'
        ]
        
class BriefedResultSerializer(serializers.ModelSerializer):
    examscore = serializers.SerializerMethodField()
    student_score = serializers.SerializerMethodField()
    issucceeded = serializers.BooleanField(source='is_succeeded')
    exam_title = serializers.SerializerMethodField()
    trials = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = [
            'id',
            'exam',
            'exam_title',
            'examscore',
            'student_score',
            'trial',
            'is_trials_finished',
            'issucceeded',
            'added',
            'trials'
        ]

    def get_exam_title(self, obj):
        return obj.exam.title if obj.exam else None

    def get_examscore(self, obj):
        # Fetch exam_score from the active trial
        active_trial = obj.active_trial
        return active_trial.exam_score if active_trial else 0

    def get_student_score(self, obj):
        # Fetch student_score from the active trial
        active_trial = obj.active_trial
        return active_trial.score if active_trial else 0

    def get_trials(self, obj):
        trials = obj.trials.all()
        return ResultTrialSerializer(trials, many=True).data

class FlattenedExamResultSerializer(serializers.ModelSerializer):
    # Exam fields with prefixed names
    exam_id = serializers.IntegerField(source='id')
    exam_title = serializers.CharField(source='title')
    exam_description = serializers.CharField(source='description')
    exam_number_of_allowed_trials = serializers.IntegerField(source='number_of_allowed_trials')
    course_title = serializers.SerializerMethodField()
    unit_title = serializers.SerializerMethodField()
    video_title = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    passing_percent = serializers.FloatField()
    exam_time_limit = serializers.IntegerField(source='time_limit')
    
    # Result fields
    examscore = serializers.SerializerMethodField()
    student_score = serializers.SerializerMethodField()
    trial = serializers.SerializerMethodField()
    is_trials_finished = serializers.SerializerMethodField()
    issucceeded = serializers.SerializerMethodField()
    trials = serializers.SerializerMethodField()
    result_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam
        fields = [
            'result_id',
            'exam_id',
            'exam_title',
            'exam_description',
            'course_title',
            'unit_title',
            'video_title',
            'year',
            'passing_percent',
            'exam_time_limit',
            'examscore',
            'student_score',
            'exam_number_of_allowed_trials',
            'trial',
            'is_trials_finished',
            'issucceeded',
            'trials'
        ]
    
    def get_course_title(self, obj):
        if obj.unit:
            return obj.unit.course.name
        elif obj.video:
            return obj.video.unit.course.name
        return None
    
    def get_unit_title(self, obj):
        if obj.unit:
            return obj.unit.name
        elif obj.video:
            return obj.video.unit.name
        return None
    
    def get_video_title(self, obj):
        if obj.video:
            return obj.video.name
        return None
    
    def get_year(self, obj):
        if obj.unit:
            return obj.unit.course.year.id
        elif obj.video:
            return obj.video.unit.course.year.id
        return None
    
    def get_result_id(self, obj):
        # Get the student_id from the context (set in the view)
        student_id = self.context.get('student_id')
        if not student_id:
            return None
        
        # Find the result for this exam and student
        try:
            result = Result.objects.get(exam=obj, student_id=student_id)
            return result.id
        except Result.DoesNotExist:
            return None
        except Result.MultipleObjectsReturned:
            # If there are multiple results, return the first one
            return Result.objects.filter(exam=obj, student_id=student_id).first().id
    
    def get_examscore(self, obj):
        result = self._get_result_for_student(obj)
        active_trial = result.active_trial if result else None
        return active_trial.exam_score if active_trial else 0
    
    def get_student_score(self, obj):
        result = self._get_result_for_student(obj)
        active_trial = result.active_trial if result else None
        return active_trial.score if active_trial else 0
    
    def get_trial(self, obj):
        result = self._get_result_for_student(obj)
        return result.trial if result else None
    
    def get_is_trials_finished(self, obj):
        result = self._get_result_for_student(obj)
        return result.is_trials_finished if result else False
    
    def get_issucceeded(self, obj):
        result = self._get_result_for_student(obj)
        return result.is_succeeded if result else False
    
    def get_trials(self, obj):
        result = self._get_result_for_student(obj)
        trials = result.trials.all() if result else []
        return ResultTrialSerializer(trials, many=True).data
    
    def _get_result_for_student(self, obj):
        # Get the student_id from the context (set in the view)
        student_id = self.context.get('student_id')
        if not student_id:
            return None
        
        # Find the result for this exam and student
        try:
            return Result.objects.get(exam=obj, student_id=student_id)
        except Result.DoesNotExist:
            return None
        except Result.MultipleObjectsReturned:
            # If there are multiple results, return the first one
            return Result.objects.filter(exam=obj, student_id=student_id).first()



class StudentFlatSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='id')
    student_user__username = serializers.CharField(source='user.username')
    student_name = serializers.CharField(source='name')
    student_parent_phone = serializers.CharField(source='parent_phone')
    student_type_education = serializers.IntegerField(source='type_education.id')
    student_year_id = serializers.IntegerField(source='year.id')
    student_government = serializers.CharField(source='government')
    student_code = serializers.CharField(source='code')
    student_jwt_token = serializers.CharField(source='jwt_token')
    student_is_center = serializers.BooleanField(source='is_center')

    class Meta:
        model = Student
        fields = [
            'student_id',
            'student_user__username',
            'student_name',
            'student_parent_phone',
            'student_type_education',
            'student_year_id',
            'student_government',
            'student_code',
            'student_jwt_token',
            'student_is_center',
        ]


class FlattenedStudentResultSerializer(serializers.ModelSerializer):
    # Student fields with prefixed names
    student_id = serializers.IntegerField(source='id')
    student_user__username = serializers.CharField(source='user.username')
    student_name = serializers.CharField(source='name')
    student_parent_phone = serializers.CharField(source='parent_phone')
    student_type_education = serializers.IntegerField(source='type_education.id')
    student_year_id = serializers.IntegerField(source='year.id')
    student_government = serializers.CharField(source='government')
    student_code = serializers.CharField(source='code')
    student_jwt_token = serializers.CharField(source='jwt_token')
    student_is_center = serializers.BooleanField(source='is_center')
    
    # Result fields
    exam_id = serializers.SerializerMethodField()
    exam_title = serializers.SerializerMethodField()
    examscore = serializers.SerializerMethodField()
    student_score = serializers.SerializerMethodField()
    trial = serializers.SerializerMethodField()
    is_trials_finished = serializers.SerializerMethodField()
    issucceeded = serializers.SerializerMethodField()
    trials = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'student_id',
            'student_user__username',
            'student_name',
            'student_parent_phone',
            'student_type_education',
            'student_year_id',
            'student_government',
            'student_code',
            'student_jwt_token',
            'student_is_center',
            'exam_id',
            'exam_title',
            'examscore',
            'student_score',
            'trial',
            'is_trials_finished',
            'issucceeded',
            'trials'
        ]
    
    def get_exam_id(self, obj):
        # Get the first result for this exam (as per context)
        result = self._get_result_for_exam(obj)
        return result.exam.id if result else None
    
    def get_exam_title(self, obj):
        result = self._get_result_for_exam(obj)
        return result.exam.title if result and result.exam else None
    
    def get_examscore(self, obj):
        result = self._get_result_for_exam(obj)
        active_trial = result.active_trial if result else None
        return active_trial.exam_score if active_trial else 0
    
    def get_student_score(self, obj):
        result = self._get_result_for_exam(obj)
        active_trial = result.active_trial if result else None
        return active_trial.score if active_trial else 0
    
    def get_trial(self, obj):
        result = self._get_result_for_exam(obj)
        return result.trial if result else None
    
    def get_is_trials_finished(self, obj):
        result = self._get_result_for_exam(obj)
        return result.is_trials_finished if result else False
    
    def get_issucceeded(self, obj):
        result = self._get_result_for_exam(obj)
        return result.is_succeeded if result else False
    
    def get_trials(self, obj):
        result = self._get_result_for_exam(obj)
        trials = result.trials.all() if result else []
        return ResultTrialSerializer(trials, many=True).data
    
    def _get_result_for_exam(self, obj):
        # Get the exam from the context (set in the view)
        exam_id = self.context.get('exam_id')
        if not exam_id:
            return None
        
        # Find the result for this exam
        try:
            return obj.result_set.get(exam_id=exam_id)
        except Result.DoesNotExist:
            return None
        except Result.MultipleObjectsReturned:
            # If there are multiple results, return the first one
            return obj.result_set.filter(exam_id=exam_id).first()



class CombinedStudentResultSerializer(serializers.ModelSerializer):
    result = BriefedResultSerializer(source='result_set', many=True, read_only=True)
    student = StudentSerializer(source='*')

    class Meta:
        model = Student
        fields = [
            'student',
            'result'
        ]


class CopyExamSerializer(serializers.Serializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all(), required=False, allow_null=True)
    video = serializers.PrimaryKeyRelatedField(queryset=Video.objects.all(), required=False, allow_null=True)
    related_to = serializers.ChoiceField(choices=RelatedToChoices.choices)

class ExamQuestionReorderSerializer(serializers.Serializer):
    exam_question = serializers.IntegerField(help_text="ID of the ExamQuestion instance.")
    # Use IntegerField for new_order, then validate it's positive
    new_order = serializers.IntegerField(help_text="The new order value for the ExamQuestion.")

    def validate_exam_question(self, value):
        try:
            ExamQuestion.objects.get(id=value)
        except ExamQuestion.DoesNotExist:
            raise serializers.ValidationError(f"ExamQuestion with ID {value} does not exist.")
        return value

    def validate_new_order(self, value):
        if value < 1:
            raise serializers.ValidationError("New order must be a positive integer.")
        return value


class ExamQuestionSerializer(serializers.ModelSerializer):
    exam_question_id = serializers.IntegerField(source='id')
    question = QuestionSerializer()

    class Meta:
        model = ExamQuestion
        fields = ['exam_question_id', 'question']

    def to_representation(self, instance):
        # Get the default representation
        representation = super().to_representation(instance)
        question_data = representation.pop('question')  # Remove nested question
        question_data['exam_question_id'] = representation['exam_question_id']  # Add exam_question_id to it
        return question_data



#^ < ==============================[ <- video quiz -> ]============================== > ^#

class VideoQuizSerializer(serializers.ModelSerializer):
    # Custom read-only fields from related objects
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    exam_start = serializers.DateTimeField(source='exam.start', read_only=True)
    exam_end = serializers.DateTimeField(source='exam.end', read_only=True)

    course_name = serializers.CharField(source='course.name', read_only=True)

    video_name = serializers.CharField(source='video.name', read_only=True)
    video_video_duration = serializers.IntegerField(source='video.video_duration', read_only=True)


    class Meta:
        model = VideoQuiz
        fields = [
            'id', 'time', 'created', 'updated',
            # Related info
            'exam', 'course', 'video',
            'exam_title', 'exam_start', 'exam_end',
            'course_name',
            'video_name', 'video_video_duration',
        ]
    
    def validate(self, data):
        """
        Check if there is already a VideoQuiz with the same video and time.
        """
        video = data.get('video')
        time = data.get('time')
        
        # Skip validation if we're updating an existing instance
        if self.instance:
            existing_quiz = VideoQuiz.objects.filter(
                video=video,
                time=time
            ).exclude(id=self.instance.id).first()
        else:
            existing_quiz = VideoQuiz.objects.filter(
                video=video,
                time=time
            ).first()
            
        if existing_quiz:
            raise serializers.ValidationError(
                "يوجد اختبار بنفس الدرس والوقت. يرجى اختيار وقت مختلف."
            )
            
        return data

#^ < ==============================[ <- Student Temp Exams -> ]============================== > ^#

class TempExamAllowedTimesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempExamAllowedTimes
        fields = ['number_of_allowedtempexams_per_day']


    def validate_number_of_allowedtempexams_per_day(self, value):
        if value < 0:
            raise serializers.ValidationError("Number of allowed temp exams per day cannot be negative.")
        return value





