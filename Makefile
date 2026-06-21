.PHONY: install test lint run

# Sync the full dev environment. Dev tooling lives in [dependency-groups], so we
# pull all groups; --all-extras covers any future [project.optional-dependencies].
install:
	uv sync --all-extras --all-groups

test:
	uv run pytest

lint:
	uv run ruff check tkstatistics/ tests/

run:
	uv run tkstatistics
