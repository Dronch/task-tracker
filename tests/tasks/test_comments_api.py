import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.tasks.models import Comment
from apps.users.models import User
from tests.factories import CommentFactory, TaskFactory

pytestmark = pytest.mark.django_db


def test_nested_comment_crud_sets_author(
    auth_client: APIClient,
    user: User,
) -> None:
    task = TaskFactory()
    list_url = reverse("tasks:comment-list", args=(task.pk,))

    response = auth_client.post(list_url, {"body": "Created through API"})
    assert response.status_code == status.HTTP_201_CREATED
    comment_id = response.data["id"]
    comment = Comment.objects.get(pk=comment_id)
    assert comment.author == user
    assert comment.task == task

    detail_url = reverse("tasks:comment-detail", args=(task.pk, comment_id))
    list_response = auth_client.get(list_url)
    detail_response = auth_client.get(detail_url)
    assert [item["id"] for item in list_response.data["results"]] == [comment_id]
    assert detail_response.data["id"] == comment_id

    response = auth_client.patch(detail_url, {"body": "Updated"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["body"] == "Updated"

    response = auth_client.delete(detail_url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Comment.objects.filter(pk=comment_id).exists()
    assert Comment.all_objects.filter(pk=comment_id).exists()


def test_comment_is_not_available_through_another_task(
    auth_client: APIClient,
) -> None:
    comment = CommentFactory()
    another_task = TaskFactory()

    response = auth_client.get(
        reverse("tasks:comment-detail", args=(another_task.pk, comment.pk))
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_comments_of_removed_task_are_unavailable(auth_client: APIClient) -> None:
    comment = CommentFactory()
    task = comment.task
    task.soft_delete()

    response = auth_client.get(reverse("tasks:comment-list", args=(task.pk,)))

    assert response.status_code == status.HTTP_404_NOT_FOUND
