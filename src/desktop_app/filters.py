import django_filters
from django.db.models import OuterRef, Subquery, IntegerField, Value, F,Q
from exam.models import Exam




class ExamFilter(django_filters.FilterSet):
    teacher = django_filters.NumberFilter(method="filter_by_teacher")

    class Meta:
        model = Exam
        fields = []

    def filter_by_teacher(self, queryset, name, value):
        return queryset.filter(
            Q(unit__course__teacher_id=value) |
            Q(video__unit__course__teacher_id=value)
        )