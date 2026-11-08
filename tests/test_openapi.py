from pathlib import Path

import pytest
import yaml
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_schema_generation_and_custom_actions(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.yaml"

    call_command(
        "spectacular",
        file=str(schema_path),
        validate=True,
        fail_on_warn=True,
    )
    schema = yaml.safe_load(schema_path.read_text())

    assert "/api/v1/tasks/{id}/complete/" in schema["paths"]
    assert "/api/v1/tasks/{id}/reopen/" in schema["paths"]
    assert "/api/v1/tasks/{id}/history/" in schema["paths"]
    assert "/api/v1/auth/logout/" in schema["paths"]
    assert "search" in {
        parameter["name"]
        for parameter in schema["paths"]["/api/v1/tasks/"]["get"]["parameters"]
    }
    assert schema["components"]["securitySchemes"]["jwtAuth"]["scheme"] == "bearer"


def test_schema_and_swagger_are_public(api_client: APIClient) -> None:
    assert api_client.get(reverse("schema")).status_code == status.HTTP_200_OK
    assert api_client.get(reverse("swagger-ui")).status_code == status.HTTP_200_OK
