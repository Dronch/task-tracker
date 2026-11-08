from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.tasks.api.v1.serializers import (
    CommentSerializer,
    TaskHistoryEntrySerializer,
    TaskSerializer,
)
from apps.tasks.filters import TaskFilter, TaskSearchFilterBackend
from apps.tasks.history import get_task_history
from apps.tasks.models import Comment, Task
from apps.tasks.services import complete_task, reopen_task

TASK_NOT_FOUND_RESPONSE = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Task not found.",
    examples=[
        OpenApiExample(
            "Task not found",
            value={"detail": "Not found."},
            response_only=True,
            status_codes=["404"],
        ),
    ],
)

TASK_LIST_PARAMETERS = [
    OpenApiParameter(
        name="status",
        type=str,
        enum=Task.Status.values,
        description="Filter by task status.",
    ),
    OpenApiParameter(
        name="priority",
        type=str,
        enum=Task.Priority.values,
        description="Filter by task priority.",
    ),
    OpenApiParameter(
        name="creator",
        type=OpenApiTypes.INT,
        description="Filter by creator user ID.",
    ),
    OpenApiParameter(
        name="assignee",
        type=OpenApiTypes.INT,
        description="Filter by assignee user ID.",
    ),
    OpenApiParameter(
        name="completed",
        type=OpenApiTypes.BOOL,
        description="Filter by whether completed_at is set.",
    ),
    OpenApiParameter(
        name="due_date_after",
        type=OpenApiTypes.DATETIME,
        description="Return tasks due at or after this datetime.",
    ),
    OpenApiParameter(
        name="due_date_before",
        type=OpenApiTypes.DATETIME,
        description="Return tasks due at or before this datetime.",
    ),
    OpenApiParameter(
        name="ordering",
        type=str,
        description=(
            "Order by created_at, updated_at, due_date, or priority. "
            "Prefix a field with '-' for descending order."
        ),
    ),
    OpenApiParameter(
        name="search",
        type=str,
        description=(
            "PostgreSQL full-text search over title and description, "
            "ordered by relevance."
        ),
    ),
]


@extend_schema_view(
    list=extend_schema(
        summary="List tasks",
        parameters=TASK_LIST_PARAMETERS,
    ),
    create=extend_schema(summary="Create a task"),
    retrieve=extend_schema(summary="Retrieve a task"),
    update=extend_schema(summary="Replace a task"),
    partial_update=extend_schema(summary="Update a task"),
    destroy=extend_schema(
        summary="Remove a task",
        responses={204: None},
    ),
)
class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
        TaskSearchFilterBackend,
    )
    filterset_class = TaskFilter
    ordering_fields = ("created_at", "updated_at", "due_date", "priority")
    ordering = ("-created_at",)

    def get_queryset(self) -> QuerySet[Task]:
        return Task.objects.select_related(
            "creator",
            "assignee",
            "completed_by",
        )

    def perform_create(self, serializer: TaskSerializer) -> None:
        serializer.save(
            creator=self.request.user,
            _history_user=self.request.user,
        )

    def perform_update(self, serializer: TaskSerializer) -> None:
        serializer.save(_history_user=self.request.user)

    def perform_destroy(self, instance: Task) -> None:
        instance.soft_delete(history_user=self.request.user)

    @extend_schema(
        summary="Complete a task",
        request=None,
        responses={
            200: TaskSerializer,
            404: TASK_NOT_FOUND_RESPONSE,
        },
    )
    @action(detail=True, methods=("post",))
    def complete(self, request: Request, pk: str | None = None) -> Response:
        task = complete_task(task=self.get_object(), completed_by=request.user)
        return Response(self.get_serializer(task).data)

    @extend_schema(
        summary="Reopen a task",
        request=None,
        responses={
            200: TaskSerializer,
            404: TASK_NOT_FOUND_RESPONSE,
        },
    )
    @action(detail=True, methods=("post",))
    def reopen(self, request: Request, pk: str | None = None) -> Response:
        task = reopen_task(task=self.get_object(), reopened_by=request.user)
        return Response(self.get_serializer(task).data)

    @extend_schema(
        summary="List task history",
        responses={
            200: TaskHistoryEntrySerializer(many=True),
            404: TASK_NOT_FOUND_RESPONSE,
        },
    )
    @action(detail=True, methods=("get",), pagination_class=None)
    def history(self, request: Request, pk: str | None = None) -> Response:
        entries = get_task_history(self.get_object())
        serializer = TaskHistoryEntrySerializer(entries, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List task comments"),
    create=extend_schema(summary="Create a task comment"),
    retrieve=extend_schema(summary="Retrieve a task comment"),
    update=extend_schema(summary="Replace a task comment"),
    partial_update=extend_schema(summary="Update a task comment"),
    destroy=extend_schema(
        summary="Remove a task comment",
        responses={204: None},
    ),
)
class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    ordering = ("created_at",)
    _task: Task

    def get_task(self) -> Task:
        if not hasattr(self, "_task"):
            self._task = get_object_or_404(
                Task.objects.select_related("creator", "assignee", "completed_by"),
                pk=self.kwargs["task_id"],
            )
        return self._task

    def get_queryset(self) -> QuerySet[Comment]:
        return (
            Comment.objects.filter(task=self.get_task())
            .select_related(
                "task",
                "author",
            )
            .order_by("created_at")
        )

    def perform_create(self, serializer: CommentSerializer) -> None:
        serializer.save(
            task=self.get_task(),
            author=self.request.user,
            _history_user=self.request.user,
        )

    def perform_update(self, serializer: CommentSerializer) -> None:
        serializer.save(_history_user=self.request.user)

    def perform_destroy(self, instance: Comment) -> None:
        instance.soft_delete(history_user=self.request.user)
