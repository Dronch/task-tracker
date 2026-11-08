import pytest
from django.urls import NoReverseMatch, reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.tasks.history import get_task_history
from apps.tasks.models import Task
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_history_contains_actor_date_event_and_diff(
    auth_client: APIClient,
    user: User,
) -> None:
    create_response = auth_client.post(
        reverse("tasks:task-list"),
        {"title": "History task"},
    )
    task_id = create_response.data["id"]
    auth_client.patch(
        reverse("tasks:task-detail", args=(task_id,)),
        {"status": Task.Status.IN_PROGRESS},
    )

    response = auth_client.get(reverse("tasks:task-history", args=(task_id,)))

    assert response.status_code == status.HTTP_200_OK
    assert [entry["event"] for entry in response.data] == ["changed", "created"]
    assert response.data[0]["actor"]["id"] == user.pk
    assert response.data[0]["occurred_at"]
    assert response.data[0]["changes"] == [
        {"field": "status", "old": "new", "new": "in_progress"}
    ]


def test_history_classifies_completion_reopen_and_removal(
    auth_client: APIClient,
) -> None:
    create_response = auth_client.post(
        reverse("tasks:task-list"),
        {"title": "Workflow history"},
    )
    task_id = create_response.data["id"]
    auth_client.post(reverse("tasks:task-complete", args=(task_id,)))
    auth_client.post(reverse("tasks:task-reopen", args=(task_id,)))

    response = auth_client.get(reverse("tasks:task-history", args=(task_id,)))
    assert [entry["event"] for entry in response.data[:3]] == [
        "reopened",
        "completed",
        "created",
    ]

    auth_client.delete(reverse("tasks:task-detail", args=(task_id,)))
    removed_task = Task.all_objects.get(pk=task_id)
    assert get_task_history(removed_task)[0]["event"] == "removed"
    assert (
        auth_client.get(reverse("tasks:task-history", args=(task_id,))).status_code
        == status.HTTP_404_NOT_FOUND
    )


def test_comment_history_has_no_public_route() -> None:
    with pytest.raises(NoReverseMatch):
        reverse("tasks:comment-history", args=(1, 1))
