import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.tasks.models import Task
from apps.users.models import User
from tests.factories import TaskFactory

pytestmark = pytest.mark.django_db


def test_create_task_sets_creator_and_assignee(
    auth_client: APIClient,
    user: User,
    other_user: User,
) -> None:
    response = auth_client.post(
        reverse("tasks:task-list"),
        {
            "title": "Created through API",
            "description": "Description",
            "assignee": other_user.pk,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    task = Task.objects.get(pk=response.data["id"])
    assert task.creator == user
    assert task.assignee == other_user
    assert response.data["creator"]["id"] == user.pk
    assert response.data["assignee"]["id"] == other_user.pk


def test_update_task_and_clear_assignee(
    auth_client: APIClient,
    other_user: User,
) -> None:
    task = TaskFactory(assignee=other_user)

    response = auth_client.patch(
        reverse("tasks:task-detail", args=(task.pk,)),
        {"title": "Updated", "status": Task.Status.READY, "assignee": None},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.title == "Updated"
    assert task.status == Task.Status.READY
    assert task.assignee is None


def test_blank_task_title_is_rejected(auth_client: APIClient) -> None:
    response = auth_client.post(reverse("tasks:task-list"), {"title": "   "})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "title" in response.data


def test_delete_task_hides_it_from_api(auth_client: APIClient) -> None:
    task = TaskFactory()
    detail_url = reverse("tasks:task-detail", args=(task.pk,))

    response = auth_client.delete(detail_url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert auth_client.get(detail_url).status_code == status.HTTP_404_NOT_FOUND
    assert not Task.objects.filter(pk=task.pk).exists()
    assert Task.all_objects.filter(pk=task.pk, removed_at__isnull=False).exists()
