import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.tasks.models import Task
from apps.users.models import User
from tests.factories import TaskFactory

pytestmark = pytest.mark.django_db


def test_complete_and_reopen_do_not_change_status(
    auth_client: APIClient,
    user: User,
) -> None:
    task = TaskFactory(status=Task.Status.IN_PROGRESS)

    response = auth_client.post(reverse("tasks:task-complete", args=(task.pk,)))
    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.completed_at is not None
    assert task.completed_by == user
    assert task.status == Task.Status.IN_PROGRESS

    response = auth_client.post(reverse("tasks:task-reopen", args=(task.pk,)))
    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.completed_at is None
    assert task.completed_by is None
    assert task.status == Task.Status.IN_PROGRESS


def test_complete_and_reopen_are_idempotent(auth_client: APIClient) -> None:
    task = TaskFactory()
    complete_url = reverse("tasks:task-complete", args=(task.pk,))
    reopen_url = reverse("tasks:task-reopen", args=(task.pk,))

    auth_client.post(complete_url)
    complete_history_count = task.history.count()
    auth_client.post(complete_url)
    assert task.history.count() == complete_history_count

    auth_client.post(reopen_url)
    reopen_history_count = task.history.count()
    auth_client.post(reopen_url)
    assert task.history.count() == reopen_history_count
