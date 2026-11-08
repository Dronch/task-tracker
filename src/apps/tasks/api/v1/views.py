from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from apps.tasks.api.v1.serializers import CommentSerializer, TaskSerializer
from apps.tasks.filters import TaskFilter
from apps.tasks.models import Comment, Task


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
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
        task = Task(
            creator=self.request.user,
            **serializer.validated_data,
        )
        task._history_user = self.request.user
        task.save()
        serializer.instance = task

    def perform_update(self, serializer: TaskSerializer) -> None:
        serializer.instance._history_user = self.request.user
        serializer.save()

    def perform_destroy(self, instance: Task) -> None:
        instance.soft_delete(history_user=self.request.user)


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
        comment = Comment(
            task=self.get_task(),
            author=self.request.user,
            **serializer.validated_data,
        )
        comment._history_user = self.request.user
        comment.save()
        serializer.instance = comment

    def perform_update(self, serializer: CommentSerializer) -> None:
        serializer.instance._history_user = self.request.user
        serializer.save()

    def perform_destroy(self, instance: Comment) -> None:
        instance.soft_delete(history_user=self.request.user)
