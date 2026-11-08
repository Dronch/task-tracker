from typing import cast

from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.tasks.models import Task
from apps.tasks.querysets import TaskQuerySet


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


class TaskSearchFilterBackend(BaseFilterBackend):
    search_param = "search"

    def filter_queryset(
        self,
        request: Request,
        queryset: QuerySet[Task],
        _view: APIView,
    ) -> QuerySet[Task]:
        value = request.query_params.get(self.search_param, "").strip()
        if not value:
            return queryset
        return cast(TaskQuerySet, queryset).search(value)
