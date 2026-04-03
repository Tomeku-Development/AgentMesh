.PHONY: up down logs test-unit test-int test-chaos demo benchmark clean install lint

install:
	cd mesh && pip install -e ".[dev]"
	cd dashboard && npm install

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

test-unit:
	cd mesh && python -m pytest ../tests/unit -v --tb=short

test-int:
	cd mesh && python -m pytest ../tests/integration -v --tb=short

test-chaos:
	cd mesh && python -m pytest ../tests/chaos -v --tb=short -s

test: test-unit

demo:
	docker compose up --build -d
	@echo "Dashboard: http://localhost:3000"
	@echo "Running demo scenario..."
	python scripts/run_demo.py

benchmark:
	python scripts/benchmark.py

clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf mesh/*.egg-info .pytest_cache

lint:
	cd mesh && python -m ruff check .
	cd mesh && python -m ruff format --check .
