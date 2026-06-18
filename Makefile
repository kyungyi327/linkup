.PHONY: default
default: run

.PHONY: run
run:
	uv run main.py

.PHONY: fix
fix:
	uv run ruff check --fix .
	uv run ruff format .

.PHONY: check
check:
	uv run ruff format --check .
	uv run ruff check .

.PHONY: lint
lint:
	uv run ruff check . --fix
	
.PHONY: format
format:
	uv run ruff format .

.PHONY: test
test:
	uv run python -m unittest discover -s tests
