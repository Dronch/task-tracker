from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.tasks.models import Task
from tests.factories import TaskFactory, UserFactory

pytestmark = pytest.mark.django_db


def result_ids(response: Response) -> list[int]:
    return [item["id"] for item in response.data["results"]]


def test_task_list_is_paginated(auth_client: APIClient) -> None:
    TaskFactory.create_batch(21)

    response = auth_client.get(reverse("tasks:task-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 21
    assert len(response.data["results"]) == 20
    assert response.data["next"] is not None


def test_all_task_filters(auth_client: APIClient) -> None:
    creator = UserFactory()
    assignee = UserFactory()
    now = timezone.now()
    target = TaskFactory(
        creator=creator,
        assignee=assignee,
        status=Task.Status.READY,
        priority=Task.Priority.HIGH,
        due_date=now,
        completed_at=now,
        completed_by=creator,
    )
    TaskFactory(
        status=Task.Status.NEW,
        priority=Task.Priority.LOW,
        due_date=None,
    )
    url = reverse("tasks:task-list")
    filters = (
        {"status": Task.Status.READY},
        {"priority": Task.Priority.HIGH},
        {"creator": creator.pk},
        {"assignee": assignee.pk},
        {"completed": "true"},
        {"due_date_after": (now - timedelta(hours=1)).isoformat()},
        {"due_date_before": (now + timedelta(hours=1)).isoformat()},
    )

    for query in filters:
        response = auth_client.get(url, query)
        assert result_ids(response) == [target.pk], query


def test_allowed_and_forbidden_ordering(auth_client: APIClient) -> None:
    older = TaskFactory(title="A", priority=Task.Priority.LOW)
    newer = TaskFactory(title="Z", priority=Task.Priority.HIGH)
    url = reverse("tasks:task-list")

    response = auth_client.get(url, {"ordering": "priority"})
    assert result_ids(response) == [newer.pk, older.pk]

    response = auth_client.get(url, {"ordering": "title"})
    assert result_ids(response) == [newer.pk, older.pk]


def test_full_text_search_ranks_title_and_excludes_removed(
    auth_client: APIClient,
) -> None:
    title_match = TaskFactory(title="galaxyuniqueterm in title", description="")
    description_match = TaskFactory(
        title="Unrelated",
        description="galaxyuniqueterm in description",
    )
    removed_match = TaskFactory(title="galaxyuniqueterm removed")
    removed_match.soft_delete()
    TaskFactory(title="No match", description="No relevant words")

    response = auth_client.get(
        reverse("tasks:task-list"),
        {"search": "GALAXYUNIQUETERM"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert result_ids(response) == [title_match.pk, description_match.pk]


def test_removed_tasks_are_excluded_from_list(auth_client: APIClient) -> None:
    active = TaskFactory()
    removed = TaskFactory()
    removed.soft_delete()

    response = auth_client.get(reverse("tasks:task-list"))

    assert result_ids(response) == [active.pk]
