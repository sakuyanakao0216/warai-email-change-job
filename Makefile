.PHONY: install-dev fmt check

install-dev:
	pip install -r requirements-dev.txt

fmt:
	black .
	isort --profile black .

check:
	black --check .
	isort --profile black --check-only .
	ruff check .
	mypy main.py
	pytest --cov=. --cov-report=term-missing --cov-fail-under=40
	pip-audit
