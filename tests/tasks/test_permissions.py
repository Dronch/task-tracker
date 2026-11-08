import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.permissions import READ_ONLY_GROUP_NAME
from apps.users.models import User
from tests.factories import CommentFactory, TaskFactory, UserFactory

pytestmark = pytest.mark.django_db


def authenticate(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_read_only_user_can_read_but_cannot_write() -> None:
    user = UserFactory()
    user.groups.add(Group.objects.get(name=READ_ONLY_GROUP_NAME))
    task = TaskFactory()
    client = authenticate(user)

    assert client.get(reverse("tasks:task-detail", args=(task.pk,))).status_code == 200
    response = client.post(reverse("tasks:task-list"), {"title": "Forbidden"})
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_regular_user_can_change_other_users_resources() -> None:
    user = UserFactory()
    task = TaskFactory()
    comment = CommentFactory(task=task)
    client = authenticate(user)

    task_response = client.patch(
        reverse("tasks:task-detail", args=(task.pk,)),
        {"title": "Changed by another user"},
    )
    comment_response = client.patch(
        reverse("tasks:comment-detail", args=(task.pk, comment.pk)),
        {"body": "Changed by another user"},
    )

    assert task_response.status_code == status.HTTP_200_OK
    assert comment_response.status_code == status.HTTP_200_OK


def test_superuser_can_write_even_in_read_only_group() -> None:
    user = UserFactory(is_staff=True, is_superuser=True)
    user.groups.add(Group.objects.get(name=READ_ONLY_GROUP_NAME))
    client = authenticate(user)

    response = client.post(reverse("tasks:task-list"), {"title": "Allowed"})

    assert response.status_code == status.HTTP_201_CREATED
