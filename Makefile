.PHONY: default run lint verify check

default: run

run:
	uv run main.py

check: lint verify

lint:
	uv run ruff check . --fix
	uv run ruff format .

verify:
	uv run python -m unittest discover -s tests
