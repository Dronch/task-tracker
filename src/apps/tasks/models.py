from typing import ClassVar

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from apps.common.models import TimeStampedSoftDeleteModel
from apps.tasks.managers import AllTasksManager, TaskHistoryManager, TaskManager
from apps.tasks.querysets import TaskHistoricalQuerySet
from apps.tasks.search import TASK_SEARCH_VECTOR


class Task(TimeStampedSoftDeleteModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        READY = "ready", "Ready"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.NEW,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority,
        default=Priority.MEDIUM,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="completed_tasks",
        null=True,
        blank=True,
    )

    objects = TaskManager()
    all_objects = AllTasksManager()
    history = HistoricalRecords(
        history_manager=TaskHistoryManager,
        historical_queryset=TaskHistoricalQuerySet,
    )

    class Meta(TimeStampedSoftDeleteModel.Meta):
        indexes: ClassVar[list[models.Index]] = [
            *TimeStampedSoftDeleteModel.Meta.indexes,
            models.Index(
                fields=("-created_at",),
                condition=models.Q(removed_at__isnull=True),
                name="tasks_active_created_idx",
            ),
            models.Index(
                fields=("status", "priority", "-created_at"),
                condition=models.Q(removed_at__isnull=True),
                name="tasks_status_priority_idx",
            ),
            models.Index(
                fields=("due_date",),
                condition=models.Q(
                    removed_at__isnull=True,
                    due_date__isnull=False,
                ),
                name="tasks_active_due_idx",
            ),
            GinIndex(
                TASK_SEARCH_VECTOR,
                name="tasks_search_vector_gin_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()

        if not self.title.strip():
            raise ValidationError({"title": "Title cannot be blank."})

        completion_fields_are_consistent = (self.completed_at is None) == (
            self.completed_by_id is None
        )
        if not completion_fields_are_consistent:
            raise ValidationError(
                {
                    "completed_at": (
                        "completed_at and completed_by must be set or cleared together."
                    ),
                    "completed_by": (
                        "completed_at and completed_by must be set or cleared together."
                    ),
                }
            )


class Comment(TimeStampedSoftDeleteModel):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        db_index=False,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="task_comments",
    )
    body = models.TextField()

    history = HistoricalRecords()

    class Meta(TimeStampedSoftDeleteModel.Meta):
        indexes: ClassVar[list[models.Index]] = [
            *TimeStampedSoftDeleteModel.Meta.indexes,
            models.Index(
                fields=("task", "created_at"),
                condition=models.Q(removed_at__isnull=True),
                name="comments_task_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Comment {self.pk} on task {self.task_id}"

    def clean(self) -> None:
        super().clean()

        if not self.body.strip():
            raise ValidationError({"body": "Comment body cannot be blank."})
