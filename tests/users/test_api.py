import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_obtain_verify_refresh_and_rotation(api_client: APIClient) -> None:
    user = UserFactory(username="auth-user")

    response = api_client.post(
        reverse("users:token-obtain-pair"),
        {"username": user.username, "password": "password"},
    )
    assert response.status_code == status.HTTP_200_OK
    access = response.data["access"]
    refresh = response.data["refresh"]

    response = api_client.post(reverse("users:token-verify"), {"token": access})
    assert response.status_code == status.HTTP_200_OK

    response = api_client.post(reverse("users:token-refresh"), {"refresh": refresh})
    assert response.status_code == status.HTTP_200_OK
    assert {"access", "refresh"} <= set(response.data)

    response = api_client.post(reverse("users:token-refresh"), {"refresh": refresh})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_blacklists_refresh_token(
    auth_client: APIClient,
    user: User,
    api_client: APIClient,
) -> None:
    refresh = str(RefreshToken.for_user(user))

    response = auth_client.post(reverse("users:logout"), {"refresh": refresh})
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = api_client.post(reverse("users:token-refresh"), {"refresh": refresh})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_business_api_requires_authentication(api_client: APIClient) -> None:
    response = api_client.get(reverse("tasks:task-list"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
