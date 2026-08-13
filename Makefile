# Enterprise AI Support Agent — local developer commands
.PHONY: setup dev migrate seed test eval lint format generate-client docker-up docker-down help

PYTHON ?= python3
PIP ?= pip3
NPM ?= npm
COMPOSE ?= docker compose -f infra/docker-compose.yml
API_DIR := apps/api
WEB_DIR := apps/web

help:
	@echo "Targets: setup dev migrate seed test eval lint format generate-client docker-up docker-down"

setup:
	@command -v $(PYTHON) >/dev/null || (echo "Python 3.12+ required" && exit 1)
	@$(PYTHON) -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" || (echo "Python 3.12+ required" && exit 1)
	@command -v node >/dev/null || (echo "Node 20+ recommended for web" && true)
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; else echo ".env already exists (not overwritten)"; fi
	@if [ -f $(API_DIR)/pyproject.toml ]; then \
		cd $(API_DIR) && $(PIP) install -e ".[dev]" 2>/dev/null || $(PIP) install -e .; \
	elif [ -f pyproject.toml ]; then \
		$(PIP) install -e ".[dev]" 2>/dev/null || $(PIP) install -e .; \
	fi
	@if [ -f $(WEB_DIR)/package.json ]; then \
		cd $(WEB_DIR) && ($(NPM) ci 2>/dev/null || $(NPM) install); \
	fi
	@if command -v docker >/dev/null 2>&1; then \
		$(COMPOSE) up -d postgres redis qdrant minio 2>/dev/null || echo "Docker infra start skipped/failed; using remote DATABASE_URL if set"; \
	else \
		echo "Docker not available; expecting DATABASE_URL (e.g. Neon) in .env"; \
	fi
	@$(MAKE) migrate || echo "migrate skipped (API/DB not ready)"
	@$(MAKE) seed || echo "seed skipped (API/DB not ready)"
	@echo "Setup complete."

dev:
	@bash scripts/dev.sh

migrate:
	@if [ -f $(API_DIR)/alembic.ini ]; then \
		cd $(API_DIR) && alembic upgrade head; \
	elif [ -d $(API_DIR)/alembic ]; then \
		cd $(API_DIR) && PYTHONPATH=. alembic upgrade head; \
	else \
		echo "No Alembic config yet; skipping migrate"; \
	fi

seed:
	@if [ -f $(API_DIR)/scripts/seed.py ]; then \
		cd $(API_DIR) && PYTHONPATH=. $(PYTHON) scripts/seed.py; \
	elif [ -f scripts/seed.py ]; then \
		$(PYTHON) scripts/seed.py; \
	else \
		echo "Seed script not found yet; skipping"; \
	fi

test:
	@if [ -d $(API_DIR)/tests ]; then \
		cd $(API_DIR) && PYTHONPATH=. pytest tests/unit -q --tb=short 2>/dev/null || PYTHONPATH=. pytest -q --tb=short; \
	else \
		$(PYTHON) -m pytest -q --tb=short; \
	fi
	@if [ -f $(WEB_DIR)/package.json ]; then \
		cd $(WEB_DIR) && $(NPM) test --if-present; \
	fi

eval:
	@if [ -f evals/run_eval.py ]; then \
		$(PYTHON) evals/run_eval.py --smoke; \
	elif [ -f $(API_DIR)/scripts/run_eval.py ]; then \
		cd $(API_DIR) && PYTHONPATH=. $(PYTHON) scripts/run_eval.py --smoke; \
	else \
		$(PYTHON) -c "from evals.graders.deterministic import smoke; smoke()"; \
	fi

lint:
	@ruff check apps packages services evals 2>/dev/null || true
	@if [ -f $(API_DIR)/pyproject.toml ]; then \
		cd $(API_DIR) && (mypy app 2>/dev/null || pyright 2>/dev/null || true); \
	fi
	@if [ -f $(WEB_DIR)/package.json ]; then \
		cd $(WEB_DIR) && $(NPM) run lint --if-present && $(NPM) run typecheck --if-present; \
	fi

format:
	@ruff format apps packages services evals 2>/dev/null || true
	@ruff check --fix apps packages services evals 2>/dev/null || true
	@if [ -f $(WEB_DIR)/package.json ]; then \
		cd $(WEB_DIR) && $(NPM) run format --if-present; \
	fi

generate-client:
	@bash scripts/generate-client.sh 2>/dev/null || \
		(echo "Generating OpenAPI client when API is available..." && \
		 curl -sf http://localhost:8000/openapi.json -o /tmp/openapi.json && \
		 npx --yes openapi-typescript /tmp/openapi.json -o packages/sdk-typescript/src/generated/schema.ts || \
		 echo "generate-client: start API or add scripts/generate-client.sh")

docker-up:
	$(COMPOSE) up -d --build

docker-down:
	$(COMPOSE) down
