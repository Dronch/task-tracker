# Task Tracker API

A Django REST API for managing tasks, assignments, comments, completion, and
change history. It uses PostgreSQL full-text search, JWT authentication, and a
versioned `/api/v1/` interface.

## Features

- Task and nested comment CRUD
- Task assignment, priorities, and `new` - `in_progress` - `ready` statuses
- Completion and reopening independently of task status
- Search, filtering, ordering, and pagination
- Per-task change history with actors and field-level diffs
- JWT obtain, refresh, verify, and logout with refresh-token revocation
- Authenticated write access and a Django-managed `read_only` group
- Public OpenAPI schema and Swagger UI

## Stack

Django 6, Django REST Framework, PostgreSQL, Simple JWT, django-simple-history,
drf-spectacular, pytest, Ruff, uv, and Docker Compose.

## Quick start

Requirements: Docker with Docker Compose.

```bash
cp .env.example .env
make up
make migrate
```

The API is available at `http://localhost:8000/api/v1/`.

- Swagger UI: http://localhost:8000/api/docs/
- OpenAPI schema: http://localhost:8000/api/schema/
- Django Admin: http://localhost:8000/admin/

Create an administrator when needed:

```bash
make superuser
```

Users and membership in the `read_only` group are managed through Django Admin.
Stop the local services with `make down`.

## Demo workflow

With the application running, execute:

```bash
make demo
```

The command creates or updates three local users:

- `demo-writer` creates and manages tasks;
- `demo-assignee` moves an assigned task through its statuses and comments;
- `demo-reader` demonstrates read-only access.

It then drives the running service exclusively through HTTP: authenticating the
users, creating and assigning a task, updating statuses, working with comments,
searching and filtering, completing and reopening the task, reading its history,
checking permissions, and removing temporary resources. Each request, actor,
status code, and expected outcome is printed. One active task is left for
inspection.

## Authentication

Obtain an access and refresh token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo-writer","password":"demo-password"}'
```

Use the returned access token for business endpoints:

```bash
curl http://localhost:8000/api/v1/tasks/ \
  -H 'Authorization: Bearer <access-token>'
```

Swagger documents the complete request and response contract.

## Development

Python 3.13 and [uv](https://docs.astral.sh/uv/) are required for local tooling.
Initialize a freshly cloned repository with:

```bash
make init
```

Useful commands:

```bash
make format             # Apply Ruff fixes and formatting
make check              # Run Ruff and Django system checks
make test               # Run pytest against PostgreSQL with coverage
make migrations         # Generate model migrations
make migrations-check   # Confirm that model changes have migrations
make schema-check       # Validate OpenAPI and fail on warnings
make pre-commit         # Run all pre-commit hooks
```

Run a smaller test selection when iterating:

```bash
make test PYTEST_ARGS=tests/tasks/test_history_api.py
```

Application configuration is read from `.env`; `.env.example` contains the
local defaults. PostgreSQL data is stored in a Docker volume.
