from django.db.models import QuerySet
from django_filters import rest_framework as filters

from apps.tasks.models import Task


class TaskFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Task.Status.choices)
    priority = filters.ChoiceFilter(choices=Task.Priority.choices)
    creator = filters.NumberFilter(field_name="creator_id")
    assignee = filters.NumberFilter(field_name="assignee_id")
    completed = filters.BooleanFilter(method="filter_completed")
    due_date_after = filters.IsoDateTimeFilter(
        field_name="due_date",
        lookup_expr="gte",
    )
    due_date_before = filters.IsoDateTimeFilter(
        field_name="due_date",
        lookup_expr="lte",
    )

    class Meta:
        model = Task
        fields: tuple[str, ...] = ()

    def filter_completed(
        self,
        queryset: QuerySet[Task],
        _name: str,
        value: bool | None,
    ) -> QuerySet[Task]:
        if value is None:
            return queryset
        return queryset.filter(completed_at__isnull=not value)
