# RestFrameWork lib
import random
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Case, When, BooleanField, Sum, Subquery, OuterRef, IntegerField
from django.db.models.functions import Coalesce
from core.permissions import HasValidAPIKey
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Prefetch
import logging
# custom filters
from exam.filters import RelatedCourseFilterBackend
#celery
from celery import shared_task
from student.models import Year
# Models
from .serializers import QuestionSerializerWithCorrectAnswer, QuestionSerializerWithoutCorrectAnswer, StudentBankSerializer, StudentExamResultSerializer, VideoQuizResultSerializer
from .models import AddReasonChoices, Answer, EssaySubmission, Exam, ExamModel, ExamModelQuestion, ExamQuestion, ExamType, Question, QuestionType, Result, ResultTrial, StudentBank, Submission, TempExam, TempExamAllowedTimes, VideoQuiz, VideoQuizResult
from course.models import Course,  Unit, Video
from subscription.models import CourseSubscription

class CheckExamStartAbility(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id):
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # Check exam time status
        exam_status = exam.status()
        if exam_status != "active":
            return Response(
                {"status": exam_status},
                status=status.HTTP_200_OK
            )
        
        # Check if result exists without creating one
        try:
            result = Result.objects.get(student=student, exam=exam)
            
            # Check for unsubmitted trial
            unsubmitted_trial = (
                result.trials
                .filter(trial=result.trial)  # Only check the current/last trial
                .filter(student_submitted_exam_at__isnull=True)
                .first()
            )
            
            if unsubmitted_trial:
                return Response({
                    "status": "unsubmitted_trial",
                    "trial": {
                        "id": unsubmitted_trial.id,
                        "trial_number": unsubmitted_trial.trial,
                        "started_at": unsubmitted_trial.student_started_exam_at,
                        "exam_model_id": unsubmitted_trial.exam_model.id if unsubmitted_trial.exam_model else None
                    }
                }, status=status.HTTP_200_OK)
            
            # Check if trials are finished
            if result.is_trials_finished:
                return Response(
                    {"status": "trials_finished"},
                    status=status.HTTP_200_OK
                )
            
        except Result.DoesNotExist:
            # No result exists, so student can start fresh
            pass
        
        # If all checks pass, user can start the exam
        return Response(
            {"status": "can_start"},
            status=status.HTTP_200_OK
        )

class StartExam(APIView):
    permission_classes = [IsAuthenticated]

    def _has_active_subscription(self, student, course):
        return CourseSubscription.objects.filter(student=student, course=course, active=True).exists()

    def _get_exam_questions(self, exam, result):
        if exam.type == ExamType.RANDOM:
            return self._get_random_exam_questions(exam, result)
        else:
            return self._get_manual_exam_questions(exam)

    def _get_random_exam_questions(self, exam, result):
        exam_models = ExamModel.objects.filter(exam=exam, is_active=True)
        if not exam_models.exists():
            return Response(
                {"error": "No models available for this random exam"},
                status=status.HTTP_400_BAD_REQUEST
            )

        exam_model = exam_models.order_by('?').first()
        result.exam_model = exam_model
        result.save()

        questions = [mq.question for mq in exam_model.model_questions.filter(is_active=True)]
        if exam.show_questions_in_random:
            random.shuffle(questions)  # Shuffle the questions
        return questions, exam_model

    def _get_manual_exam_questions(self, exam):
        questions = [eq.question for eq in ExamQuestion.objects.filter(exam=exam, question__is_active=True)]
        if exam.show_questions_in_random:
            random.shuffle(questions)  # Shuffle the questions
        return questions, None

    def get(self, request, exam_id: int) -> Response:
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)
        course = get_object_or_404(Course, id=exam.get_related_course())

        # Verify subscription (if needed)
        # if not self._has_active_subscription(student, course):
        #     return Response(
        #         {"error": "You do not have access permissions"},
        #         status=status.HTTP_401_UNAUTHORIZED,
        #     )

        # Ensure the exam is active
        exam_status = exam.status()
        if exam_status != "active":
            return Response(
                {"error": f"Exam is {exam_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create Result
        result, created = Result.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={'trial': 0}
        )

        # Check if trials are finished
        if not created and result.is_trials_finished:
            return Response(
                {"error": "You have finished your allowed trials for this exam"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for an unsubmitted trial
        unsubmitted_trial = result.trials.filter(student_submitted_exam_at__isnull=True).order_by('-trial').first()

        if unsubmitted_trial:
            # Use the existing unsubmitted trial
            result_trial = unsubmitted_trial
            questions, exam_model = self._get_exam_questions(exam, result)
            if exam_model and not result_trial.exam_model:
                result_trial.exam_model = exam_model
                result_trial.save()

            # Serialize questions
            question_data = [QuestionSerializerWithoutCorrectAnswer(q).data for q in questions]

            return Response(
                {
                    "exam_id": exam.id,
                    "exam_title": exam.title,
                    "exam_time_limit": exam.time_limit,
                    "questions": question_data,
                    "exam_model": {
                        "id": exam_model.id,
                        "title": exam_model.title
                    } if exam_model else None,
                    "resuming": True,
                    "trial_id": result_trial.id,
                    "started_at": result_trial.student_started_exam_at
                },
                status=status.HTTP_200_OK
            )
        else:
            # Increment trial counter
            result.trial += 1
            result.save()

            # Create a new ResultTrial for the current trial
            result_trial = ResultTrial.objects.create(
                result=result,
                trial=result.trial,
                student_started_exam_at=timezone.now()
            )

            # Fetch questions based on exam type
            questions, exam_model = self._get_exam_questions(exam, result)
            if exam_model:
                result_trial.exam_model = exam_model
                result_trial.save()

            # Serialize questions
            question_data = [QuestionSerializerWithoutCorrectAnswer(q).data for q in questions]

            return Response(
                {
                    "exam_id": exam.id,
                    "exam_title": exam.title,
                    "exam_time_limit": exam.time_limit,
                    "questions": question_data,
                    "exam_model": {
                        "id": exam_model.id,
                        "title": exam_model.title
                    } if exam_model else None,
                    "resuming": False,
                    "trial_id": result_trial.id
                },
                status=status.HTTP_200_OK
            )

class SubmitExam(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, exam_id):
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)
        submit_type = request.data.get("submit_type", "student_submit")

        # Get all unique question IDs from the request
        question_ids = set()
        for key in request.data.keys():
            if key.startswith('question_id_'):
                question_ids.add(int(key.split('_')[-1]))
            elif key == 'question_id':  # Handle case where it's not numbered
                question_ids.add(int(request.data[key]))

        # Get or create Result and ResultTrial
        result = get_object_or_404(Result, student=student, exam=exam)
        result_trial = result.trials.filter(trial=result.trial).first()
        if not result_trial:
            return Response(
                {"error": "No active trial found for this exam"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process each question
        for question_id in question_ids:
            question = get_object_or_404(Question, pk=question_id)
            if question.question_type == QuestionType.MCQ:
                # Process MCQ answer
                selected_answer_id = request.data.get(f"selected_answer_id_{question_id}")
                # Handle null/empty string case
                if selected_answer_id in [None, "", "null"]:
                    # Always create new submission with no answer
                    Submission.objects.create(
                        student=student,
                        exam=exam,
                        question=question,
                        result_trial=result_trial,
                        selected_answer=None,
                        is_solved=False,
                        is_correct=False
                    )
                    StudentBank.objects.get_or_create(
                        student=student,
                        question=question,
                        defaults={"add_reason": AddReasonChoices.UNSOLVED}
                    )
                    continue
                try:
                    selected_answer = get_object_or_404(
                        Answer,
                        pk=selected_answer_id,
                        question=question
                    )
                    # Always create new submission with the selected answer
                    Submission.objects.create(
                        student=student,
                        exam=exam,
                        question=question,
                        result_trial=result_trial,
                        selected_answer=selected_answer,
                        is_solved=True,
                        is_correct=selected_answer.is_correct
                    )
                    if not Submission.is_correct:
                        StudentBank.objects.get_or_create(
                            student=student,
                            question=question,
                            defaults={"add_reason": AddReasonChoices.INCORRECT}
                        )
                except (ValueError, status.HTTP_404_NOT_FOUND):
                    # Handle invalid answer ID
                    # Always create new submission with no answer
                    Submission.objects.create(
                        student=student,
                        exam=exam,
                        question=question,
                        result_trial=result_trial,
                        selected_answer=None,
                        is_solved=False,
                        is_correct=False
                    )
                    StudentBank.objects.get_or_create(
                        student=student,
                        question=question,
                        defaults={"add_reason": AddReasonChoices.UNSOLVED}
                    )
            elif question.question_type == QuestionType.ESSAY:
                # Process Essay answer
                essay_answer_text = request.data.get(f"essay_answer_text_{question_id}", "")
                # Handle file upload
                essay_answer_file = request.FILES.get(f"essay_file_{question_id}")
                # Always create new essay submission
                EssaySubmission.objects.create(
                    student=student,
                    exam=exam,
                    question=question,
                    result_trial=result_trial,
                    answer_text=essay_answer_text,
                    answer_file=essay_answer_file,
                    is_scored=False,
                    score=None
                )

        # Calculate scores
        try:
            # Calculate MCQ score
            mcq_score = Submission.objects.filter(
                result_trial=result_trial,
                is_correct=True
            ).aggregate(total=Sum('question__points'))['total'] or 0

            # Calculate essay score (only scored essays)
            essay_score = EssaySubmission.objects.filter(
                result_trial=result_trial,
                is_scored=True
            ).aggregate(total=Sum('score'))['total'] or 0

            total_score = mcq_score + essay_score

            # Get exam total score
            if result.exam.type == ExamType.RANDOM and result_trial.exam_model:
                exam_score = ExamModelQuestion.objects.filter(
                    exam_model=result_trial.exam_model
                ).aggregate(total=Sum('question__points'))['total'] or 0
            else:
                exam_score = Question.objects.filter(
                    exam_questions__exam=result.exam,
                    is_active=True
                ).aggregate(total=Sum('points'))['total'] or 0

            # Update trial and result
            result_trial.score = total_score
            result_trial.exam_score = exam_score
            result_trial.student_submitted_exam_at = timezone.now()
            result_trial.submit_type = submit_type
            result_trial.save()

            result.score = total_score
            result.save()

        except Exception as e:
            return Response(
                {"error": f"Error calculating score: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "message": "Exam submitted successfully",
            "score": total_score,
            "is_succeeded": total_score >= (exam.passing_percent / 100) * result_trial.exam_score,
            "trial": result.trial
        }, status=status.HTTP_200_OK)


class StudentExamResultsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentExamResultSerializer
    filter_backends = [DjangoFilterBackend, RelatedCourseFilterBackend]
    filterset_fields = ['exam__unit', 'exam__video', 'exam__related_to']

    def get_queryset(self):
        student = self.request.user.student
        now = timezone.now()

        return Result.objects.filter(student=student).select_related(
            'exam', 
            # 'exam__unit',  # Commented out as not needed
            # 'exam__video',  # Commented out as not needed
            'student',
            'student__user',
            'exam_model'
        ).prefetch_related(
            Prefetch(
                'trials',
                queryset=ResultTrial.objects.order_by('-trial')
                    .select_related('exam_model')
            ),
            Prefetch(
                'exam__exam_questions',
                queryset=ExamQuestion.objects.select_related('question')
                    .filter(question__is_active=True)
            ),
            # Prefetch(  # Commented out as not needed
            #     'exam__submissions',
            #     queryset=Submission.objects.filter(student=student)
            #         .select_related('question', 'selected_answer', 'result_trial')
            # ),
            Prefetch(
                'exam_model__model_questions',
                queryset=ExamModelQuestion.objects.all(),
                to_attr='prefetched_model_questions'
            )
        ).annotate(
            # is_allowed_to_show_result=Case(  # Commented out as not needed
            #     When(exam__allow_show_results_at__lte=now, then=True),
            #     default=False,
            #     output_field=BooleanField()
            # ),
            # is_allowed_to_show_answers=Case(  # Commented out as not needed
            #     When(exam__allow_show_answers_at__isnull=True, then=False),
            #     When(exam__allow_show_answers_at__lte=now, then=True),
            #     default=False,
            #     output_field=BooleanField()
            # )
        ).order_by('-added')

class GetMyExamResult(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id):
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)

        # Ensure result visibility
        # if timezone.now() < exam.allow_show_results_at:
        #     return Response(
        #         {"error": "You are not allowed to see this exam result yet"},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        # Fetch the result and active trial
        result = get_object_or_404(Result, student=student, exam=exam)
        active_trial = result.active_trial

        # Fetch MCQ submissions and prefetch correct answers for each question
        mcq_submissions = Submission.objects.filter(
            student=student, exam=exam, result_trial=active_trial
        ).select_related(
            'question', 'selected_answer', 'question__category'
        ).prefetch_related(
            Prefetch(
                'question__answers',
                queryset=Answer.objects.filter(is_correct=True),
                to_attr='correct_answers_list'  # Custom attribute to store the result
            )
        )

        # Fetch Essay submissions
        essay_submissions = EssaySubmission.objects.filter(
            student=student, exam=exam, result_trial=active_trial
        ).select_related('question', 'question__category')

        # Calculate counts
        correct_mcq_count = mcq_submissions.filter(is_correct=True).count()
        incorrect_mcq_count = mcq_submissions.filter(is_correct=False, is_solved=True).count()
        unsolved_mcq_count = mcq_submissions.filter(is_solved=False).count()
        correct_essay_count = essay_submissions.filter(is_scored=True, score__gt=0).count()
        incorrect_essay_count = essay_submissions.filter(is_scored=True, score=0).count()
        unscored_essay_count = essay_submissions.filter(is_scored=False).count()

        student_answers = []
        unsolved_questions = []
        unscored_essay_questions = []

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            selected_answer = submission.selected_answer

            # Fetch all answers for the question
            answers = Answer.objects.filter(question=question)
            answer_details = [
                {
                    "id": ans.id,
                    "text": ans.text,
                    "image": ans.image.url if ans.image else None,
                    "is_correct": ans.is_correct
                }
                for ans in answers
            ]

            # Construct the selected answer object
            selected_answer_obj = None
            if selected_answer:
                selected_answer_obj = {
                    "id": submission.selected_answer.id,
                    "text": selected_answer.text,
                    "image": selected_answer.image.url if selected_answer.image else None,
                    "is_correct": selected_answer.is_correct
                }

            answer_data = {
                "submission_id": submission.id,
                "type": "mcq",
                "question_id": question.id if question else None,
                "question_category": question.category.title if question and question.category else None,
                "question_category_id": question.category.id if question and question.category else None,
                "question_text": question.text if question else None,
                "question_image": question.image.url if question and question.image else None,
                "question_comment": question.comment,
                "selected_answer": selected_answer_obj,  # Updated to include full object
                "is_correct": submission.is_correct if submission.is_correct is not None else False,
                "is_solved": submission.is_solved if submission.is_solved is not None else False,
                "points": question.points,
                "answers": answer_details  # Include all answers here
            }
            student_answers.append(answer_data)

            # if not submission.is_solved:
            #     unsolved_questions.append(answer_data)

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = {
                "submission_id": submission.id,
                "type": "essay",
                "question_id": question.id if question else None,
                "question_category": question.category.title if question and question.category else None,
                "question_category_id": question.category.id if question and question.category else None,
                "question_text": question.text if question else None,
                "question_image": question.image.url if question and question.image else None,
                "question_comment": question.comment,
                "answer_text": submission.answer_text,
                "answer_file": submission.answer_file.url if submission.answer_file else None,
                "score": submission.score,
                "is_scored": submission.is_scored,
                "points": question.points,
            }
            student_answers.append(answer_data)

            # if not submission.is_scored:
            #     unscored_essay_questions.append(answer_data)

        # Fetch correct answers (can be kept for a separate summary if needed)
        questions = Question.objects.filter(exam_questions__exam=exam).distinct()
        correct_answers_summary = [
            {
                "question_id": question.id,
                "question_text": question.text,
                "question_image": question.image.url if question.image else None,
                "question_type": question.question_type,
                "question_comment": question.comment,
                "correct_answers": [
                    {"text": answer.text, "image": answer.image.url if answer.image else None}
                    for answer in question.answers.filter(is_correct=True)
                ],
            }
            for question in questions
        ]

        # Response payload
        response_data = {
            "active_trial": active_trial.id,
            "trial_number": active_trial.trial,
            "exam_id": exam.id,
            "exam_title": exam.title,
            "exam_description": exam.description,
            "exam_score": active_trial.exam_score if active_trial else 0,
            "student_score": active_trial.score if active_trial else 0,
            "is_succeeded": result.is_succeeded,
            "student_trials": result.trial,
            "is_trials_finished": result.is_trials_finished,
            # Counts
            "number_of_essay": essay_submissions.count(),
            "number_of_mcq": mcq_submissions.count(),
            "correct_mcq_count": correct_mcq_count,
            "incorrect_mcq_count": incorrect_mcq_count,
            "unsolved_mcq_count": unsolved_mcq_count,
            "correct_essay_count": correct_essay_count,
            "incorrect_essay_count": incorrect_essay_count,
            "unscored_essay_count": unscored_essay_count,
            # Other data
            "student_answers": student_answers,
            # "unsolved_questions": unsolved_questions,
            # "unscored_essay_questions": unscored_essay_questions,
            # "correct_answers_summary": correct_answers_summary, # Renamed for clarity
            "student_started_exam_at": active_trial.student_started_exam_at if active_trial else None,
            "student_submitted_exam_at": active_trial.student_submitted_exam_at if active_trial else None,
            "submit_type": active_trial.submit_type if active_trial else None,
        }

        return Response(response_data, status=status.HTTP_200_OK)

class GetMyExamResultForTrial(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id, result_trial_id):
        student = request.user.student
        exam = get_object_or_404(Exam, pk=exam_id)

        # Fetch the specific trial and ensure it belongs to the student and exam
        trial = get_object_or_404(
            ResultTrial.objects.select_related('result', 'result__exam', 'result__student'),
            pk=result_trial_id,
            result__student=student,
            result__exam=exam
        )

        # Fetch MCQ submissions and prefetch correct answers for each question
        mcq_submissions = Submission.objects.filter(
            student=student, exam=exam, result_trial=trial
        ).select_related(
            'question', 'selected_answer', 'question__category'
        ).prefetch_related(
            Prefetch(
                'question__answers',
                queryset=Answer.objects.filter(is_correct=True),
                to_attr='correct_answers_list'
            )
        )

        # Fetch Essay submissions
        essay_submissions = EssaySubmission.objects.filter(
            student=student, exam=exam, result_trial=trial
        ).select_related('question', 'question__category')

        # Calculate counts
        correct_mcq_count = mcq_submissions.filter(is_correct=True).count()
        incorrect_mcq_count = mcq_submissions.filter(is_correct=False, is_solved=True).count()
        unsolved_mcq_count = mcq_submissions.filter(is_solved=False).count()
        correct_essay_count = essay_submissions.filter(is_scored=True, score__gt=0).count()
        incorrect_essay_count = essay_submissions.filter(is_scored=True, score=0).count()
        unscored_essay_count = essay_submissions.filter(is_scored=False).count()

        student_answers = []

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            selected_answer = submission.selected_answer

            # Fetch all answers for the question
            answers = Answer.objects.filter(question=question)
            answer_details = [
                {
                    "id": ans.id,
                    "text": ans.text,
                    "image": ans.image.url if ans.image else None,
                    "is_correct": ans.is_correct
                }
                for ans in answers
            ]

            # Construct the selected answer object
            selected_answer_obj = None
            if selected_answer:
                selected_answer_obj = {
                    "id": submission.selected_answer.id,
                    "text": selected_answer.text,
                    "image": selected_answer.image.url if selected_answer.image else None,
                    "is_correct": selected_answer.is_correct
                }

            answer_data = {
                "submission_id": submission.id,
                "type": "mcq",
                "question_id": question.id if question else None,
                "question_category": question.category.title if question and question.category else None,
                "question_category_id": question.category.id if question and question.category else None,
                "question_text": question.text if question else None,
                "question_image": question.image.url if question and question.image else None,
                "question_comment": question.comment,
                "selected_answer": selected_answer_obj,
                "is_correct": submission.is_correct if submission.is_correct is not None else False,
                "is_solved": submission.is_solved if submission.is_solved is not None else False,
                "points": question.points,
                "answers": answer_details
            }
            student_answers.append(answer_data)

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = {
                "submission_id": submission.id,
                "type": "essay",
                "question_id": question.id if question else None,
                "question_category": question.category.title if question and question.category else None,
                "question_category_id": question.category.id if question and question.category else None,
                "question_text": question.text if question else None,
                "question_image": question.image.url if question and question.image else None,
                "question_comment": question.comment,
                "answer_text": submission.answer_text,
                "answer_file": submission.answer_file.url if submission.answer_file else None,
                "score": submission.score,
                "is_scored": submission.is_scored,
                "points": question.points,
            }
            student_answers.append(answer_data)

        # Fetch correct answers (can be kept for a separate summary if needed)
        questions = Question.objects.filter(exam_questions__exam=exam).distinct()
        correct_answers_summary = [
            {
                "question_id": question.id,
                "question_text": question.text,
                "question_image": question.image.url if question.image else None,
                "question_type": question.question_type,
                "question_comment": question.comment,
                "correct_answers": [
                    {"text": answer.text, "image": answer.image.url if answer.image else None}
                    for answer in question.answers.filter(is_correct=True)
                ],
            }
            for question in questions
        ]

        # Determine if the student succeeded in this trial
        is_succeeded = False
        if trial.exam_score and trial.score is not None:
            is_succeeded = trial.score >= (exam.passing_percent / 100) * trial.exam_score

        # Response payload
        response_data = {
            "active_trial": trial.id,
            "trial_number": trial.trial,
            "exam_id": exam.id,
            "exam_title": exam.title,
            "exam_description": exam.description,
            "exam_score": trial.exam_score if trial else 0,
            "student_score": trial.score if trial else 0,
            "is_succeeded": is_succeeded,
            "student_trials": trial.result.trial if trial else 0,
            "is_trials_finished": trial.result.is_trials_finished if trial else False,
            # Counts
            "number_of_essay": essay_submissions.count(),
            "number_of_mcq": mcq_submissions.count(),
            "correct_mcq_count": correct_mcq_count,
            "incorrect_mcq_count": incorrect_mcq_count,
            "unsolved_mcq_count": unsolved_mcq_count,
            "correct_essay_count": correct_essay_count,
            "incorrect_essay_count": incorrect_essay_count,
            "unscored_essay_count": unscored_essay_count,
            # Other data
            "student_answers": student_answers,
            "student_started_exam_at": trial.student_started_exam_at if trial else None,
            "student_submitted_exam_at": trial.student_submitted_exam_at if trial else None,
            "submit_type": trial.submit_type if trial else None,
            
        }

        return Response(response_data, status=status.HTTP_200_OK)


#^-------------------------------- {vIDEO qUIZ} ---------------------------------^#

class StartVideoQuiz(APIView):
    permission_classes = [IsAuthenticated]

    def _has_active_subscription(self, student, course):
        return CourseSubscription.objects.filter(student=student, course=course, active=True).exists()

    def _get_exam_questions(self, exam, result):
        if exam.type == ExamType.RANDOM:
            return self._get_random_exam_questions(exam, result)
        else:
            return self._get_manual_exam_questions(exam)

    def _get_random_exam_questions(self, exam, result):
        exam_models = ExamModel.objects.filter(exam=exam, is_active=True)
        if not exam_models.exists():
            return Response(
                {"error": "No models available for this random exam"},
                status=status.HTTP_400_BAD_REQUEST
            )

        exam_model = exam_models.order_by('?').first()
        

        questions = [mq.question for mq in exam_model.model_questions.filter(is_active=True)]
        if exam.show_questions_in_random:
            random.shuffle(questions)  
        return questions, exam_model

    def _get_manual_exam_questions(self, exam):
        questions = [eq.question for eq in ExamQuestion.objects.filter(exam=exam, question__is_active=True)]
        if exam.show_questions_in_random:
            random.shuffle(questions)  
        return questions, None

    def get(self, request, video_quiz_id: int) -> Response:
        student = request.user.student
        video_quiz = get_object_or_404(VideoQuiz, pk=video_quiz_id)
        course = video_quiz.course
        exam = video_quiz.exam

        # Verify subscription (if needed)
        if not self._has_active_subscription(student, course):
            return Response(
                {"error": "You do not have access permissions"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Ensure the exam is active
        exam_status = exam.status()
        if exam_status != "active":
            return Response(
                {"error": f"Exam is {exam_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch or create Result object
        result, created = VideoQuizResult.objects.get_or_create(
            student=student,
            video_quiz=video_quiz,
        )
        if result:
            result.trial += 1
            result.save()


        # Fetch questions based on exam type
        questions, exam_model = self._get_exam_questions(exam, result)

        # Serialize questions
        question_data = [QuestionSerializerWithCorrectAnswer(q).data for q in questions]

        return Response(
            {
                "video_quiz":video_quiz.id,
                "initial_result": result.id,
                "course":course.id,
                "course_title":course.name,
                "video":video_quiz.video.id,
                "video_title":video_quiz.video.name,
                "time":video_quiz.time,
                "exam_id": exam.id,
                "exam_score": exam.score,
                "exam_passing_percent": exam.passing_percent,
                "exam_title": exam.title,
                "exam_time_limit": exam.time_limit,
                "trial": result.trial,
                "questions": question_data,
                "exam_model": {
                    "id": exam_model.id,
                    "title": exam_model.title
                } if exam_model else None,
            },
            status=status.HTTP_200_OK
        )


class UpdateVideoQuizResultView(APIView):
    def post(self, request, *args, **kwargs):
        # Get data from request
        data = request.data
        
        try:
            # Get the initial_result to update
            instance = VideoQuizResult.objects.get(id=data.get('initial_result'))
            
            # Validate that the video_quiz and student match the instance
            if str(instance.video_quiz.id) != str(data.get('video_quiz')) :
                return Response(
                    {"error": "Video quiz or student doesn't match the initial result"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update the instance with new data
            instance.exam_score = data.get('exam_score', instance.exam_score)
            instance.student_score = data.get('student_score', instance.student_score)
            instance.save()
            
            # Serialize and return the updated instance
            serializer = VideoQuizResultSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except VideoQuizResult.DoesNotExist:
            return Response(
                {"error": "Video quiz result not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class VideoQuizResultsListView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            # Get query parameters (optional filtering)
            student_id = request.query_params.get('student_id')
            video_quiz_id = request.query_params.get('video_quiz_id')
            course_id = request.query_params.get('course_id')
            video_id = request.query_params.get('video_id')
            
            # Base queryset
            queryset = VideoQuizResult.objects.select_related(
                'student',
                'video_quiz',
                'video_quiz__exam',
                'video_quiz__course',
                'video_quiz__video'
            )
            
            # Apply filters if provided
            if student_id:
                queryset = queryset.filter(student_id=student_id)
            if video_quiz_id:
                queryset = queryset.filter(video_quiz_id=video_quiz_id)
            if course_id:
                queryset = queryset.filter(video_quiz__course_id=course_id)
            if video_id:
                queryset = queryset.filter(video_quiz__video_id=video_id)
            
            # Build response data
            results = []
            for result in queryset:
                results.append({
                    'id': result.id,
                    'student_id': result.student.id,
                    'student_name': result.student.name,
                    'student_phone': result.student.user.username,
                    'student_code': result.student.code,
                    'video_quiz_id': result.video_quiz.id,
                    'video_quiz_time': result.video_quiz.time,
                    'exam_id': result.video_quiz.exam.id if result.video_quiz.exam else None,
                    'exam_title': result.video_quiz.exam.title if result.video_quiz.exam else None,
                    'course_id': result.video_quiz.course.id if result.video_quiz.course else None,
                    'course_name': result.video_quiz.course.name if result.video_quiz.course else None,
                    'video_id': result.video_quiz.video.id,
                    'video_name': result.video_quiz.video.name,
                    'exam_score': result.exam_score,
                    'student_score': result.student_score,
                    'percentage': (result.student_score / result.exam_score * 100) if result.exam_score > 0 else 0,
                    'is_succeeded': result.is_succeeded(),
                    'passing_percent': result.video_quiz.exam.passing_percent if result.video_quiz.exam else None,
                    'trial': result.trial,
                    'added': result.added
                })
            
            return Response({'results': results}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


#^-------------------------------- {Student Temp Exams} ---------------------------------^#Add commentMore actions

class StudentBankListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentBankSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['add_reason', 'is_solved_now', 'question__question_type']
    search_fields = ['question__text']

    def get_queryset(self):
        student = self.request.user.student
        queryset = StudentBank.objects.filter(student=student)
        
        year = self.request.query_params.get('year')
        course = self.request.query_params.get('course')
        unit = self.request.query_params.get('unit')
        video = self.request.query_params.get('video')

        if year:
            queryset = queryset.filter(question__unit__course__year__id=year)
        if course:
            queryset = queryset.filter(question__unit__course__id=course)
        if unit:
            queryset = queryset.filter(question__unit__id=unit)
        if video:
            queryset = queryset.filter(question__video__id=video)

        return queryset.order_by('-created')

class CreateTempExam(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = request.user.student
        number_of_questions = request.data.get('number_of_questions')
        year = request.data.get('year')
        course = request.data.get('course')
        unit = request.data.get('unit')
        video = request.data.get('video')
        time_limit = request.data.get('time_limit', 30)  # Default 30 minutes
        selected_questions_type = request.data.get('selected_questions_type')

        # Validate input
        try:
            number_of_questions = int(number_of_questions)
            if number_of_questions <= 0:
                return Response(
                    {"error": "Number of questions must be positive"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid number of questions"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate selected_questions_type
        if selected_questions_type not in ['solved', 'not_solved', None]:
            return Response(
                {"error": "Invalid selected_questions_type. Must be 'solved', 'not_solved', or null."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate daily limit
        today = timezone.now().date()
        limit, created = TempExamAllowedTimes.objects.get_or_create(
            id=1,
            defaults={'number_of_allowedtempexams_per_day': 3}
        )
        used_attempts = TempExam.objects.filter(
            student=student,
            created__date=today
        ).count()

        if used_attempts >= limit.number_of_allowedtempexams_per_day:
            return Response(
                {"error": f"Daily temp exam limit of {limit.number_of_allowedtempexams_per_day} reached"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get MCQ questions from StudentBank
        queryset = StudentBank.objects.filter(
            student=student,
            question__question_type=QuestionType.MCQ
        )

        if selected_questions_type == 'solved':
            queryset = queryset.filter(is_solved_now=True)
        elif selected_questions_type == 'not_solved':
            queryset = queryset.filter(is_solved_now=False)

        if year:
            queryset = queryset.filter(question__unit__course__year__id=year)
        if course:
            queryset = queryset.filter(question__unit__course__id=course)
        if unit:
            queryset = queryset.filter(question__unit__id=unit)
        if video:
            queryset = queryset.filter(question__video__id=video)

        questions = list(queryset.select_related('question'))
        if len(questions) < number_of_questions:
            return Response(
                {"error": f"Not enough questions available. Found {len(questions)}, required {number_of_questions}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Randomly select questions
        selected_student_banks = random.sample(questions, number_of_questions)
        selected_questions = [sb.question for sb in selected_student_banks]

        # Create TempExam
        temp_exam = TempExam.objects.create(
            student=student,
            year=Year.objects.filter(id=year).first() if year else None,
            course=Course.objects.filter(id=course).first() if course else None,
            unit=Unit.objects.filter(id=unit).first() if unit else None,
            video=Video.objects.filter(id=video).first() if video else None,
            number_of_questions=number_of_questions,
            time_limit=time_limit,
            selected_questions_type=selected_questions_type
        )

        # Serialize questions
        question_data = [QuestionSerializerWithCorrectAnswer(q).data for q in selected_questions]

        return Response({
            "temp_exam_id": temp_exam.id,
            "number_of_questions": temp_exam.number_of_questions,
            "time_limit": temp_exam.time_limit,
            "year": temp_exam.year.id if temp_exam.year else None,
            "course": temp_exam.course.id if temp_exam.course else None,
            "unit": temp_exam.unit.id if temp_exam.unit else None,
            "video": temp_exam.video.id if temp_exam.video else None,
            "selected_questions_type": temp_exam.selected_questions_type,
            "questions": question_data
        }, status=status.HTTP_201_CREATED)

class SubmitTempExamResults(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = request.user.student
        temp_exam_id = request.data.get('temp_exam_id')
        correct_question_ids = request.data.get('correct_question_ids', [])
        result = request.data.get('result')

        temp_exam = get_object_or_404(TempExam, id=temp_exam_id, student=student)

        # Update is_solved_now for correct questions
        StudentBank.objects.filter(
            student=student,
            question__id__in=correct_question_ids
        ).update(is_solved_now=True)

        # Update TempExam result
        try:
            temp_exam.result = float(result) if result is not None else None
            temp_exam.save()
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid result format. Must be a number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "message": "Temp exam results submitted successfully",
            "temp_exam_id": temp_exam.id,
            "result": temp_exam.result
        }, status=status.HTTP_200_OK)

