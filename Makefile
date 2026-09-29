.PHONY: install dev test lint demo clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=mechpulse

lint:
	ruff check src/ tests/

demo:
	python -m mechpulse --simulate

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
