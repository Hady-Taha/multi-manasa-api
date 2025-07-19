from celery import shared_task
from django.utils.timezone import now
from .models import Course, Unit , Video

@shared_task
def update_pending_content():
    current_time = now()
    updated_count = {"videos": 0, "courses": 0, "units": 0}

    # Update Videos
    videos = Video.objects.filter(pending=True, publisher_date__lte=current_time)
    updated_count["videos"] = videos.count()
    videos.update(pending=False)

    # Update Courses
    courses = Course.objects.filter(pending=True, publisher_date__lte=current_time)
    updated_count["courses"] = courses.count()
    courses.update(pending=False)

    # Update Units
    units = Unit.objects.filter(pending=True, publisher_date__lte=current_time)
    updated_count["units"] = units.count()
    units.update(pending=False)

    return f"Updated {updated_count}"