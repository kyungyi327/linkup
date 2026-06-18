.PHONY: default
default: run

UV_RUN := uv run --locked

.PHONY: init
init:
	$(UV_RUN) --no-sync python -c "from linkup.db.repositories.db import init_db; init_db()"
	$(UV_RUN) --no-sync python -m linkup.db.tools.etl_fitteum

.PHONY: run
run:
	$(UV_RUN) main.py

.PHONY: fix
fix:
	$(UV_RUN) ruff check --fix .
	$(UV_RUN) ruff format .

.PHONY: check
check:
	$(UV_RUN) ruff format --check .
	$(UV_RUN) ruff check .
	$(MAKE) test

.PHONY: lint
lint:
	$(UV_RUN) ruff check . --fix

.PHONY: format
format:
	$(UV_RUN) ruff format .

.PHONY: coverage
coverage:
	$(UV_RUN) coverage erase
	$(UV_RUN) coverage run --source=linkup -m unittest discover -s tests
	$(UV_RUN) coverage report -m
	$(UV_RUN) coverage html

.PHONY: test
test:
	$(UV_RUN) python -m unittest discover -s tests
