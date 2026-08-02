.PHONY: install test lint typecheck check demo benchmark docker-check docker-build docker-smoke

install:
	python -m pip install -e ".[dev,mcp]"

test:
	python -m pytest

lint:
	python -m ruff check src tests

format:
	python -m ruff format src tests

typecheck:
	python -m mypy src/athena

check: lint typecheck test

demo:
	athena init examples/java-spring-demo
	athena scan examples/java-spring-demo
	athena context "Add retry logic to PaymentClient" --root examples/java-spring-demo --persona developer

benchmark:
	athena benchmark benchmarks/representative.yaml --root examples/benchmark-fixture --scan --gate

docker-check:
	docker build --check .
	docker compose config --quiet

docker-build:
	docker build --tag athena-codegraph:local .

docker-smoke: docker-build
	docker run --rm athena-codegraph:local version
