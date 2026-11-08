import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.tasks.models import Comment, Task
from tests.factories import CommentFactory, TaskFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_task_defaults_and_choices() -> None:
    task = TaskFactory()

    assert task.status == Task.Status.NEW
    assert task.priority == Task.Priority.MEDIUM

    task.status = "invalid"
    task.priority = "invalid"
    with pytest.raises(ValidationError) as error:
        task.full_clean()

    assert {"status", "priority"} <= set(error.value.message_dict)


def test_completion_fields_must_be_set_together() -> None:
    task = TaskFactory()
    task.completed_at = timezone.now()

    with pytest.raises(ValidationError) as error:
        task.full_clean()

    assert {"completed_at", "completed_by"} <= set(error.value.message_dict)

    task.completed_by = UserFactory()
    task.full_clean()


def test_soft_delete_hides_objects_and_creates_history() -> None:
    task = TaskFactory()
    comment = CommentFactory(task=task)
    task_history_count = task.history.count()
    comment_history_count = comment.history.count()

    assert task.soft_delete()
    assert comment.soft_delete()

    assert not Task.objects.filter(pk=task.pk).exists()
    assert Task.all_objects.filter(pk=task.pk, removed_at__isnull=False).exists()
    assert not Comment.objects.filter(pk=comment.pk).exists()
    assert Comment.all_objects.filter(pk=comment.pk, removed_at__isnull=False).exists()
    assert task.history.count() == task_history_count + 1
    assert comment.history.count() == comment_history_count + 1


def test_queryset_soft_delete_does_not_remove_rows() -> None:
    tasks = TaskFactory.create_batch(2)

    deleted_count = Task.objects.filter(
        pk__in=[task.pk for task in tasks]
    ).soft_delete()

    assert deleted_count == 2
    assert Task.objects.count() == 0
    assert Task.all_objects.count() == 2
