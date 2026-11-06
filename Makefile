COMPOSE = docker compose
MANAGE = $(COMPOSE) run --rm web python src/manage.py

.PHONY: \
	init sync hooks \
	up down build logs ps \
	migrate migrations migrations-check superuser shell manage \
	format lint pre-commit check

init: .env sync hooks

.env: .env.example
	cp .env.example .env

sync:
	uv sync --frozen

hooks:
	uv run pre-commit install

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f web

ps:
	$(COMPOSE) ps

migrate:
	$(MANAGE) migrate

migrations:
	$(MANAGE) makemigrations

migrations-check:
	$(MANAGE) makemigrations --check --dry-run

superuser:
	$(MANAGE) createsuperuser

shell:
	$(MANAGE) shell

manage:
	$(MANAGE) $(CMD)

format:
	uv run ruff check --fix .
	uv run ruff format .

lint:
	uv run ruff check .
	uv run ruff format --check .

pre-commit:
	uv run pre-commit run --all-files

check: lint
	uv run python src/manage.py check
