from django.db import transaction
from course.models import Unit, Course, Video, VideoFile, File
from exam.models import Exam, ExamQuestion

def copy_unit_with_subunits(source_unit, target_course, parent=None):
    """
    Recursively copy a unit and its subunits to the target course.
    """
    # Create the unit copy
    new_unit = Unit.objects.create(
        name=source_unit.name,
        description=source_unit.description,
        course=target_course,
        order=source_unit.order,
        pending=source_unit.pending,
        parent=parent,  # This is the key change to support subunits
    )

    # Copy videos
    for video in source_unit.unit_videos.all():
        new_video = Video.objects.create(
            name=video.name,
            description=video.description,
            unit=new_unit,
            can_view=video.can_view,
            views=video.views,
            duration=video.duration,
            stream_type=video.stream_type,
            stream_link=video.stream_link,
            order=video.order,
            price=video.price,
            pending=video.pending,
            publisher_date=video.publisher_date,
            ready=video.ready,
            can_buy=video.can_buy,
            free=video.free,
            points=video.points,
        )

        for video_file in video.video_files.all():
            VideoFile.objects.create(
                name=video_file.name,
                video=new_video,
                file=video_file.file,  # Reuse file
            )

    # Copy unit files
    for unit_file in source_unit.unit_files.all():
        File.objects.create(
            name=unit_file.name,
            file=unit_file.file,  # Reuse file
            unit=new_unit,
            pending=unit_file.pending,
            order=unit_file.order,
        )

    # Copy exams
    for exam in source_unit.exams.all():
        new_exam = Exam.objects.create(
            title=exam.title,
            description=exam.description,
            related_to=exam.related_to,
            unit=new_unit if exam.related_to == "UNIT" else None,
            video=None,
            course=target_course,
            number_of_questions=exam.number_of_questions,
            time_limit=exam.time_limit,
            score=exam.score,
            passing_percent=exam.passing_percent,
            start=exam.start,
            end=exam.end,
            number_of_allowed_trials=exam.number_of_allowed_trials,
            type=exam.type,
            easy_questions_count=exam.easy_questions_count,
            medium_questions_count=exam.medium_questions_count,
            hard_questions_count=exam.hard_questions_count,
            show_answers_after_finish=exam.show_answers_after_finish,
            order=exam.order,
            is_active=exam.is_active,
            allow_show_results_at=exam.allow_show_results_at,
            allow_show_answers_at=exam.allow_show_answers_at,
            is_depends=exam.is_depends,
        )

        for eq in exam.exam_questions.all():
            ExamQuestion.objects.create(
                exam=new_exam,
                question=eq.question,
                is_active=eq.is_active
            )

    # 🔁 Recurse into subunits
    for subunit in source_unit.subunits.all():
        copy_unit_with_subunits(subunit, target_course, parent=new_unit)

    return new_unit

@transaction.atomic
def copy_unit_to_course(source_unit_id, target_course_id, new_unit_name=None):
    try:
        source_unit = Unit.objects.get(id=source_unit_id)
        target_course = Course.objects.get(id=target_course_id)
    except Unit.DoesNotExist:
        raise Unit.DoesNotExist(f"Unit with ID {source_unit_id} does not exist.")
    except Course.DoesNotExist:
        raise Course.DoesNotExist(f"Course with ID {target_course_id} does not exist.")

    # Temporarily override the name if specified
    if new_unit_name:
        source_unit.name = new_unit_name

    return copy_unit_with_subunits(source_unit, target_course)