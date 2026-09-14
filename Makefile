.PHONY: install test lint run

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest

lint:
	ruff check .

run:
	python -m agent.loop
