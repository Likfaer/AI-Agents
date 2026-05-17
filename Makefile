.PHONY: install dev-backend dev-frontend dev test lint docker-up docker-down clean

# Setup
install:
	cp -n .env.example .env || true
	pip install -r backend/requirements.txt
	cd frontend && npm install

# Development
dev-backend:
	python -m backend.main

dev-frontend:
	cd frontend && npm run dev

# Run both (requires tmux or two terminals)
dev:
	@echo "Run in two separate terminals:"
	@echo "  make dev-backend"
	@echo "  make dev-frontend"

# Tests
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-coverage:
	pytest --cov=backend --cov-report=html --cov-report=term-missing

# Lint
lint:
	python -m ruff check backend/
	python -m mypy backend/ --ignore-missing-imports

# Docker
docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

# Workspace
workspace:
	mkdir -p workspace data/memory logs
