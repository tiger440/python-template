.DEFAULT_GOAL := check
.PHONY: check fix test docs-serve docs-build bench rename sync

sync:
	uv sync --all-extras

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright
	uv run pytest

fix:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build --strict

bench:
	@echo "no bench in template"

rename:
ifndef NEW
	$(error usage: make rename NEW=<project_name>)
endif
	uv run python scripts/rename_package.py $(NEW)
