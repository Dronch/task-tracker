.PHONY: init sync hooks format lint pre-commit check

init: .env sync hooks

.env: .env.example
	cp .env.example .env

sync:
	uv sync --frozen

hooks:
	uv run pre-commit install

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
