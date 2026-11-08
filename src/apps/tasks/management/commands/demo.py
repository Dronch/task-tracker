import json
import os
from collections.abc import Callable, Collection
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.common.permissions import READ_ONLY_GROUP_NAME
from apps.users.models import User


class ApiClient:
    def __init__(
        self,
        base_url: str,
        actor: str,
        token: str | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.actor = actor
        self.token = token
        self.logger = logger

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        expected_status: int | Collection[int] = 200,
        accept: str = "application/json",
        expectation: str | None = None,
    ) -> Any:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Accept": accept}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if self.token is not None:
            headers["Authorization"] = f"Bearer {self.token}"

        request = Request(
            url=f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        self._log(f"  [{self.actor}] -> {method} {path}")
        try:
            with urlopen(request, timeout=10) as response:
                status_code = response.status
                response_body = response.read()
        except HTTPError as error:
            status_code = error.code
            response_body = error.read()
        except URLError as error:
            raise CommandError(
                f"Cannot connect to API at {self.base_url}: {error.reason}"
            ) from error

        allowed_statuses = (
            {expected_status}
            if isinstance(expected_status, int)
            else set(expected_status)
        )
        data = self._decode_response(response_body)
        if status_code not in allowed_statuses:
            self._log(f"  [{self.actor}] <- {status_code} (unexpected)")
            raise CommandError(
                f"{method} {path} returned {status_code}, expected "
                f"{sorted(allowed_statuses)}: {data}"
            )
        reason = expectation or self._default_expectation(status_code)
        self._log(f"  [{self.actor}] <- {status_code} (expected: {reason})")
        return data

    def _log(self, message: str) -> None:
        if self.logger is not None:
            self.logger(message)

    @staticmethod
    def _default_expectation(status_code: int) -> str:
        reasons = {
            200: "the authenticated request should succeed",
            201: "the authenticated writer may create this resource",
            204: "the operation should succeed without a response body",
            400: "the request is invalid",
            401: "the request has no valid authentication",
            403: "the authenticated user is not allowed to write",
            404: "the resource must not be exposed by the API",
        }
        return reasons.get(status_code, "the API contract allows this status")

    @staticmethod
    def _decode_response(response_body: bytes) -> Any:
        if not response_body:
            return None
        decoded = response_body.decode()
        try:
            return json.loads(decoded)
        except json.JSONDecodeError:
            return decoded


class Command(BaseCommand):
    help = "Create demo users and exercise the task workflow through the HTTP API."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--base-url",
            default=os.getenv("DEMO_API_BASE_URL", "http://127.0.0.1:8000"),
            help="Base URL of the running API.",
        )
        parser.add_argument(
            "--password",
            default=os.getenv("DEMO_USER_PASSWORD", "demo-password"),
            help="Password assigned to demo users.",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        base_url = str(options["base_url"])
        password = str(options["password"])
        writer, assignee, reader = self._prepare_users(password)
        self._print_participants(base_url, writer, assignee, reader)
        public_client = self._api_client(base_url, "anonymous")

        self._step("Checking public documentation and authentication boundary")
        public_client.request(
            "GET",
            "/api/schema/",
            expectation="the OpenAPI schema is public",
        )
        public_client.request(
            "GET",
            "/api/docs/",
            accept="text/html",
            expectation="Swagger UI is public",
        )
        public_client.request(
            "GET",
            "/api/v1/tasks/",
            expected_status=401,
            expectation="business endpoints require JWT authentication",
        )

        writer_tokens = self._obtain_tokens(public_client, writer, password)
        writer_client = self._api_client(
            base_url,
            writer.username,
            writer_tokens["access"],
        )
        assignee_tokens = self._obtain_tokens(public_client, assignee, password)
        assignee_client = self._api_client(
            base_url,
            assignee.username,
            assignee_tokens["access"],
        )
        run_id = uuid4().hex[:10]
        search_term = f"demoflow{run_id}"

        self._step("Listing users and creating an assigned task")
        writer_client.request("GET", "/api/v1/users/?page_size=100")
        assignee_data = writer_client.request(
            "GET",
            f"/api/v1/users/{assignee.pk}/",
        )
        self._require(
            assignee_data.get("id") == assignee.pk,
            "Assignee is missing from the users API",
        )
        task = writer_client.request(
            "POST",
            "/api/v1/tasks/",
            {
                "title": f"{search_term} workflow task",
                "description": "Created by the demo management command.",
                "priority": "medium",
                "assignee": assignee.pk,
            },
            expected_status=201,
        )
        task_id = self._require_id(task, "task")
        self._require(
            task.get("assignee", {}).get("id") == assignee.pk,
            "Task was not assigned to the demo assignee",
        )
        writer_client.request("GET", f"/api/v1/tasks/{task_id}/")

        self._step("Unassigning and reassigning the task")
        updated_task = writer_client.request(
            "PATCH",
            f"/api/v1/tasks/{task_id}/",
            {"assignee": None},
        )
        self._require(updated_task.get("assignee") is None, "Task was not unassigned")
        writer_client.request(
            "PATCH",
            f"/api/v1/tasks/{task_id}/",
            {"assignee": assignee.pk},
        )

        self._step("Moving the assigned task from new to in_progress")
        assignee_client.request("GET", f"/api/v1/tasks/{task_id}/")
        assignee_client.request(
            "PATCH",
            f"/api/v1/tasks/{task_id}/",
            {"status": "in_progress", "priority": "high"},
            expectation="the assignee may move the assigned task forward",
        )

        self._step("Creating, reading, updating, listing, and removing comments")
        comments_path = f"/api/v1/tasks/{task_id}/comments/"
        comment = assignee_client.request(
            "POST",
            comments_path,
            {"body": "Comment from the assigned user"},
            expected_status=201,
            expectation="the assignee may comment on the task",
        )
        comment_id = self._require_id(comment, "comment")
        self._require(
            comment.get("author", {}).get("id") == assignee.pk,
            "Comment author is not the demo assignee",
        )
        comment_path = f"{comments_path}{comment_id}/"
        assignee_client.request("GET", comment_path)
        assignee_client.request(
            "PATCH",
            comment_path,
            {"body": "Updated comment from the assigned user"},
        )
        disposable_comment = writer_client.request(
            "POST",
            comments_path,
            {"body": "Disposable demo comment"},
            expected_status=201,
        )
        disposable_comment_id = self._require_id(disposable_comment, "comment")
        writer_client.request(
            "DELETE",
            f"{comments_path}{disposable_comment_id}/",
            expected_status=204,
        )
        writer_client.request("GET", comments_path)

        self._step("Filtering and full-text searching tasks")
        query = urlencode(
            {
                "search": search_term,
                "status": "in_progress",
                "priority": "high",
                "assignee": assignee.pk,
            }
        )
        task_list = writer_client.request("GET", f"/api/v1/tasks/?{query}")
        self._require_result(task_list, task_id)

        self._step("Moving the task from in_progress to ready")
        assignee_client.request(
            "PATCH",
            f"/api/v1/tasks/{task_id}/",
            {"status": "ready"},
            expectation="the assignee may move in_progress to ready",
        )
        assignee_client.request(
            "POST",
            "/api/v1/auth/logout/",
            {"refresh": assignee_tokens["refresh"]},
            expected_status=204,
        )

        self._step("Completing, inspecting history, and reopening the ready task")
        completed_task = writer_client.request(
            "POST",
            f"/api/v1/tasks/{task_id}/complete/",
        )
        self._require(
            completed_task.get("completed_by", {}).get("id") == writer.pk,
            "Task was not completed by the demo writer",
        )
        self._require(
            completed_task.get("status") == "ready",
            "Completion unexpectedly changed the task status",
        )
        history = writer_client.request(
            "GET",
            f"/api/v1/tasks/{task_id}/history/",
        )
        self._require_event(history, "completed")
        reopened_task = writer_client.request(
            "POST",
            f"/api/v1/tasks/{task_id}/reopen/",
        )
        self._require(
            reopened_task.get("completed_at") is None,
            "Task was not reopened",
        )
        self._require(
            reopened_task.get("status") == "ready",
            "Reopen unexpectedly changed the task status",
        )

        self._step("Checking read-only permissions")
        reader_tokens = self._obtain_tokens(public_client, reader, password)
        reader_client = self._api_client(
            base_url,
            reader.username,
            reader_tokens["access"],
        )
        reader_client.request("GET", f"/api/v1/tasks/{task_id}/")
        reader_client.request(
            "POST",
            "/api/v1/tasks/",
            {"title": "This write must be rejected"},
            expected_status=403,
            expectation="members of read_only may use only safe HTTP methods",
        )
        reader_client.request(
            "POST",
            "/api/v1/auth/logout/",
            {"refresh": reader_tokens["refresh"]},
            expected_status=204,
        )

        self._step("Removing a disposable task")
        disposable_task = writer_client.request(
            "POST",
            "/api/v1/tasks/",
            {"title": f"Disposable {run_id}"},
            expected_status=201,
        )
        disposable_task_id = self._require_id(disposable_task, "task")
        disposable_path = f"/api/v1/tasks/{disposable_task_id}/"
        writer_client.request("DELETE", disposable_path, expected_status=204)
        writer_client.request(
            "GET",
            disposable_path,
            expected_status=404,
            expectation="a removed task is hidden from subsequent API reads",
        )

        self._step("Refreshing, verifying, and revoking the writer token")
        writer_token_client = self._api_client(
            base_url,
            f"{writer.username} (refresh token)",
        )
        refreshed_tokens = writer_token_client.request(
            "POST",
            "/api/v1/auth/token/refresh/",
            {"refresh": writer_tokens["refresh"]},
            expectation="a valid refresh token should issue a new token pair",
        )
        new_access = self._require_string(refreshed_tokens, "access")
        new_refresh = self._require_string(refreshed_tokens, "refresh")
        writer_token_client.request(
            "POST",
            "/api/v1/auth/token/verify/",
            {"token": new_access},
            expectation="the newly issued access token must be valid",
        )
        refreshed_client = self._api_client(
            base_url,
            f"{writer.username} (refreshed JWT)",
            new_access,
        )
        refreshed_client.request(
            "POST",
            "/api/v1/auth/logout/",
            {"refresh": new_refresh},
            expected_status=204,
        )
        writer_token_client.request(
            "POST",
            "/api/v1/auth/token/refresh/",
            {"refresh": new_refresh},
            expected_status=401,
            expectation="logout revoked this refresh token",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo completed successfully. Active task={task_id}, "
                f"users={writer.username}, {assignee.username}, {reader.username}."
            )
        )

    def _prepare_users(self, password: str) -> tuple[User, User, User]:
        writer = self._upsert_user("demo-writer", password)
        assignee = self._upsert_user("demo-assignee", password)
        reader = self._upsert_user("demo-reader", password)
        read_only_group, _ = Group.objects.get_or_create(name=READ_ONLY_GROUP_NAME)
        writer.groups.remove(read_only_group)
        assignee.groups.remove(read_only_group)
        reader.groups.add(read_only_group)
        return writer, assignee, reader

    def _print_participants(
        self,
        base_url: str,
        writer: User,
        assignee: User,
        reader: User,
    ) -> None:
        self.stdout.write("Demo participants:")
        self.stdout.write(f"  API: {base_url}")
        self.stdout.write(
            f"  {writer.username} (id={writer.pk}): writer, full API access"
        )
        self.stdout.write(
            f"  {assignee.username} (id={assignee.pk}): assignee, moves statuses "
            "and comments"
        )
        self.stdout.write(
            f"  {reader.username} (id={reader.pk}): read_only, reads allowed, "
            "writes rejected"
        )
        self.stdout.write("")

    def _api_client(
        self,
        base_url: str,
        actor: str,
        token: str | None = None,
    ) -> ApiClient:
        return ApiClient(base_url, actor, token, logger=self.stdout.write)

    @staticmethod
    def _upsert_user(username: str, password: str) -> User:
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        user.set_password(password)
        user.save(update_fields=("password",))
        return user

    @staticmethod
    def _obtain_tokens(
        client: ApiClient,
        user: User,
        password: str,
    ) -> dict[str, str]:
        credential_client = ApiClient(
            client.base_url,
            f"{user.username} (credentials)",
            logger=client.logger,
        )
        response = credential_client.request(
            "POST",
            "/api/v1/auth/token/",
            {"username": user.username, "password": password},
            expectation="valid credentials should issue an access/refresh pair",
        )
        return {
            "access": Command._require_string(response, "access"),
            "refresh": Command._require_string(response, "refresh"),
        }

    @staticmethod
    def _require(condition: bool, message: str) -> None:
        if not condition:
            raise CommandError(message)

    @staticmethod
    def _require_string(data: Any, key: str) -> str:
        if not isinstance(data, dict) or not isinstance(data.get(key), str):
            raise CommandError(
                f"Response does not contain string field '{key}': {data}"
            )
        return data[key]

    @staticmethod
    def _require_id(data: Any, resource: str) -> int:
        if not isinstance(data, dict) or not isinstance(data.get("id"), int):
            raise CommandError(f"Response does not contain {resource} ID: {data}")
        return data["id"]

    @staticmethod
    def _require_result(data: Any, task_id: int) -> None:
        if not isinstance(data, dict):
            raise CommandError(f"Unexpected task list response: {data}")
        results = data.get("results", [])
        if not any(item.get("id") == task_id for item in results):
            raise CommandError(f"Task {task_id} is missing from filtered task list")

    @staticmethod
    def _require_event(data: Any, event: str) -> None:
        if not isinstance(data, list) or not any(
            item.get("event") == event for item in data
        ):
            raise CommandError(f"History event '{event}' is missing: {data}")

    def _step(self, message: str) -> None:
        self.stdout.write(f"- {message}")
