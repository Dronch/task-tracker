from typing import ClassVar

from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from apps.common.models import TimeStampedSoftDeleteModel


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

    history = HistoricalRecords()

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
        ]

    def __str__(self) -> str:
        return self.title


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
