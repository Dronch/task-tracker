from django.db import transaction
from django.utils import timezone

from apps.tasks.models import Task
from apps.users.models import User


def _lock_task(task: Task) -> Task:
    return (
        Task.objects.select_for_update(of=("self",))
        .select_related("creator", "assignee", "completed_by")
        .get(pk=task.pk)
    )


@transaction.atomic
def complete_task(*, task: Task, completed_by: User) -> Task:
    task = _lock_task(task)

    if task.completed_at is not None and task.completed_by_id is not None:
        return task

    task.completed_at = timezone.now()
    task.completed_by = completed_by
    task._history_user = completed_by
    task.save(update_fields=("completed_at", "completed_by", "updated_at"))
    return task


@transaction.atomic
def reopen_task(*, task: Task, reopened_by: User) -> Task:
    task = _lock_task(task)

    if task.completed_at is None and task.completed_by_id is None:
        return task

    task.completed_at = None
    task.completed_by = None
    task._history_user = reopened_by
    task.save(update_fields=("completed_at", "completed_by", "updated_at"))
    return task
