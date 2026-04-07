.PHONY: up up-logs down restart logs logs-backend logs-frontend build \
       test test-backend test-frontend \
       lint lint-backend lint-frontend fmt \
       migrate migrate-new \
       shell-backend shell-frontend shell-db \
       clean help

# ── Services ──────────────────────────────────────────────

up:                    ## Start all containers
	docker compose up -d

up-logs:               ## Start all containers with log output
	docker compose up

down:                  ## Stop all containers
	docker compose down

restart:               ## Restart all containers
	docker compose restart

build:                 ## Rebuild all containers
	docker compose build

logs:                  ## Tail logs from all containers
	docker compose logs -f

logs-backend:          ## Tail backend logs
	docker compose logs -f backend

logs-frontend:         ## Tail frontend logs
	docker compose logs -f frontend

# ── Testing ───────────────────────────────────────────────

test: test-backend test-frontend  ## Run all tests

test-backend:          ## Run backend tests (pytest)
	docker compose exec backend uv run pytest -v

test-frontend:         ## Run frontend tests (vitest)
	docker compose exec frontend pnpm test --run

# ── Linting ───────────────────────────────────────────────

lint: lint-backend lint-frontend  ## Run all linters

lint-backend:          ## Lint + format check backend (ruff)
	docker compose exec backend uv run ruff check .
	docker compose exec backend uv run ruff format --check .

lint-frontend:         ## Lint frontend (eslint)
	docker compose exec frontend pnpm lint

fmt:                   ## Auto-format backend code
	docker compose exec backend uv run ruff format .
	docker compose exec backend uv run ruff check --fix .

# ── Database ──────────────────────────────────────────────

migrate:               ## Run pending migrations
	docker compose exec backend uv run alembic upgrade head

migrate-new:           ## Create a new migration (usage: make migrate-new msg="add foo table")
	@test -n "$(msg)" || (echo "Error: msg is required. Usage: make migrate-new msg=\"add foo table\"" && exit 1)
	docker compose exec backend uv run alembic revision --autogenerate -m "$(msg)"

# ── Shells ────────────────────────────────────────────────

shell-backend:         ## Open a shell in the backend container
	docker compose exec backend bash

shell-frontend:        ## Open a shell in the frontend container
	docker compose exec frontend sh

shell-db:              ## Open psql in the postgres container
	docker compose exec postgres psql -U clinic_atlas -d clinic_atlas

# ── Cleanup ───────────────────────────────────────────────

clean:                 ## Stop containers and remove volumes
	docker compose down -v

# ── Help ──────────────────────────────────────────────────

help:                  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
