.PHONY: install test lint run harness report docker-build docker-run

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest

lint:
	ruff check .

run:
	python try_agent.py

harness:
	python run_harness.py $(PROFILE)

report:
	python generate_report.py

docker-build:
	docker build -t agentic-task-runner .

docker-run:
	docker run agentic-task-runner
