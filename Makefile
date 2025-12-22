# Environment
PYTHON := python3.12
CONFIGS_DIG := config
TOML_CONFIG_MANAGER := $(CONFIGS_DIG)/toml_config_manager.py
APP_ENV := local

.PHONY: env dotenv
env:
	@echo APP_ENV=$(APP_ENV)

venv:
	$(PYTHON) -m venv env

clean-install:
	rm -rf env
	$(PYTHON) -m venv env
	./env/bin/python -m pip install --upgrade pip setuptools wheel
	./env/bin/pip install -e .

dotenv:
	@$(PYTHON) $(TOML_CONFIG_MANAGER) ${APP_ENV}

start:
	. env/bin/activate && PYTHONPATH=src python3.12 -m uvicorn app.run:make_app --factory --host 0.0.0.0 --port 8080 --reload

# Celery
.PHONY: celery celery.worker celery.beat celery.flower
.PHONY: celery.worker.maintenance celery.worker.agents celery.worker.graph
.PHONY: celery.worker.distillation celery.worker.projects celery.worker.llm
.PHONY: celery.worker.transactions celery.worker.risk celery.worker.email
.PHONY: celery.stop

# Iniciar todos los workers, beat y flower con logs en tiempo real
celery: venv
	@./scripts/start_all_celery.sh

# Detener todos los procesos de Celery
celery.stop:
	@echo "Deteniendo todos los procesos de Celery..."
	@pkill -f "celery.*worker" || true
	@pkill -f "celery.*beat" || true
	@pkill -f "flower" || true
	@echo "✅ Todos los procesos detenidos"

# Worker general (legacy - usa todas las colas)
celery.all: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker -B --loglevel=INFO -n worker@%h

celery.worker: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker --loglevel=INFO -n worker@%h

celery.beat: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app beat --loglevel=INFO

celery.flower: venv
	PYTHONPATH=src ./env/bin/python -m flower -A app.infrastructure.celery.app.celery_app --broker=redis://localhost:6379/0 flower --address=0.0.0.0 --port=5555

# Workers especializados por cola (recomendado para producción)
# Cada worker procesa solo su cola específica para evitar latencia

# Maintenance Worker - Tareas de limpieza y mantenimiento (baja prioridad)
celery.worker.maintenance: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q maintenance \
		-n maintenance@%h \
		--concurrency=2 \
		--max-tasks-per-child=500

# Agents Worker - Procesamiento de agentes IA (alta prioridad, tiempo real)
celery.worker.agents: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q agents \
		-n agents@%h \
		--concurrency=8 \
		--max-tasks-per-child=200

# Graph Worker - Mantenimiento de grafo y embeddings (procesamiento pesado)
celery.worker.graph: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q graph \
		-n graph@%h \
		--concurrency=2 \
		--max-tasks-per-child=100

# Distillation Worker - Procesamiento de LLM y caché
celery.worker.distillation: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q distillation \
		-n distillation@%h \
		--concurrency=4 \
		--max-tasks-per-child=300

# Projects Worker - Knowledge base y proyectos
celery.worker.projects: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q projects \
		-n projects@%h \
		--concurrency=3 \
		--max-tasks-per-child=200

# LLM Worker - Ranking y orchestration de LLM
celery.worker.llm: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q llm \
		-n llm@%h \
		--concurrency=4 \
		--max-tasks-per-child=250

# Transactions Worker - Confirmación de transacciones blockchain (crítico)
celery.worker.transactions: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q transactions \
		-n transactions@%h \
		--concurrency=6 \
		--max-tasks-per-child=500

# Risk Worker - Monitoreo de riesgo
celery.worker.risk: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q risk \
		-n risk@%h \
		--concurrency=3 \
		--max-tasks-per-child=300

# Email Worker - Envío de emails
celery.worker.email: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker \
		--loglevel=INFO \
		-Q email \
		-n email@%h \
		--concurrency=2 \
		--max-tasks-per-child=1000

# Transaction Confirmation Worker
# Confirms pending blockchain transactions and updates DB status
.PHONY: worker.tx worker.tx-once worker.tx-testnet worker.tx-mainnet
worker.tx:
	@echo "Starting Transaction Confirmation Worker (loop mode)..."
	PYTHONPATH=src ./env/bin/python -m app.cli.confirm_pending_transactions --loop

worker.tx-once:
	@echo "Processing pending transactions (one-off)..."
	PYTHONPATH=src ./env/bin/python -m app.cli.confirm_pending_transactions --once

worker.tx-testnet:
	@echo "Starting Transaction Confirmation Worker (testnet)..."
	PYTHONPATH=src ./env/bin/python -m app.cli.confirm_pending_transactions --loop --testnet

worker.tx-mainnet:
	@echo "Starting Transaction Confirmation Worker (mainnet)..."
	PYTHONPATH=src ./env/bin/python -m app.cli.confirm_pending_transactions --loop --mainnet

# Docker: Transaction Confirmation Worker (standalone)
up.tx-worker: guard-APP_ENV
	@echo "Starting Transaction Confirmation Worker (Docker)..."
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) --profile tx-worker up -d tx_confirmation_worker

down.tx-worker: guard-APP_ENV
	@echo "Stopping Transaction Confirmation Worker..."
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) --profile tx-worker down

logs.tx-worker: guard-APP_ENV
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) --profile tx-worker logs -f tx_confirmation_worker

# MCP Servers
.PHONY: mcp mcp.oneinch mcp.defillama mcp.thegraph mcp.coingecko mcp.all mcp.stop
mcp: mcp.all

mcp.oneinch:
	@echo "Starting 1inch MCP Server on port 8081..."
	PYTHONPATH=src python3.12 -m app.infrastructure.mcp.servers.oneinch_mcp

mcp.defillama:
	@echo "Starting DeFiLlama MCP Server on port 8082..."
	PYTHONPATH=src python3.12 -m app.infrastructure.mcp.servers.defillama_mcp

mcp.thegraph:
	@echo "Starting The Graph MCP Server on port 8083..."
	PYTHONPATH=src python3.12 -m app.infrastructure.mcp.servers.thegraph_mcp

mcp.coingecko:
	@echo "Starting CoinGecko MCP Server on port 8084..."
	PYTHONPATH=src python3.12 -m app.infrastructure.mcp.servers.coingecko_mcp

mcp.all:
	@echo "Starting all MCP servers..."
	@echo "Note: Run each server in a separate terminal or use a process manager."
	@echo ""
	@echo "Terminal 1: make mcp.oneinch"
	@echo "Terminal 2: make mcp.defillama"
	@echo "Terminal 3: make mcp.thegraph"
	@echo "Terminal 4: make mcp.coingecko"
	@echo ""
	@echo "Or use Docker Compose: make up.mcp"

mcp.stop:
	@echo "Stopping all MCP servers..."
	@pkill -f "app.infrastructure.mcp.servers" || echo "No MCP servers running"

# MCP Servers - Docker Compose
.PHONY: up.mcp up.mcp.local up.mcp.prod down.mcp logs.mcp
up.mcp: up.mcp.local

up.mcp.local:
	@echo "Starting MCP servers (local environment)..."
	@cd $(CONFIGS_DIG)/local && $(DOCKER_COMPOSE) --env-file .env.local -f docker-compose-mcp.yml up -d

up.mcp.prod:
	@echo "Starting MCP servers (production environment)..."
	@cd $(CONFIGS_DIG)/prod && $(DOCKER_COMPOSE) --env-file .env.prod -f docker-compose-mcp.yml up -d

down.mcp:
	@echo "Stopping MCP servers..."
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) -f docker-compose-mcp.yml down

logs.mcp:
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) -f docker-compose-mcp.yml logs -f

alembic:
	. env/bin/activate && alembic init src/app/infrastructure/persistence_sqla/alembic

alembic-revision:
	. env/bin/activate && alembic -c src/app/infrastructure/persistence_sqla/alembic.ini revision --autogenerate -m "Add new table"

alembic-upgrade:
	. env/bin/activate && alembic -c src/app/infrastructure/persistence_sqla/alembic.ini upgrade head

alembic-downgrade:
	. env/bin/activate && alembic -c src/app/infrastructure/persistence_sqla/alembic.ini downgrade -1

create-db:
	. env/bin/activate && APP_ENV=$(APP_ENV) python3.12 scripts/create_db.py

init-db: create-db
	. env/bin/activate && APP_ENV=$(APP_ENV) python3.12 scripts/init_db.py

test-config:
	. env/bin/activate && APP_ENV=$(APP_ENV) python3.12 scripts/test_config.py
# Docker compose
DOCKER_COMPOSE := docker compose
DOCKER_COMPOSE_PRUNE := scripts/makefile/docker_prune.sh

.PHONY: guard-APP_ENV up.db up.db-echo up up.echo down down.total logs.db shell.db prune
guard-APP_ENV:
ifndef APP_ENV
	$(error "APP_ENV is not set. Set APP_ENV before running this command.")
endif

up.db: guard-APP_ENV
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up -d baseapi_db --build

up.db-echo: guard-APP_ENV
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up baseapi_db --build

up:
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up -d --build

up.echo:
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up --build

down: guard-APP_ENV
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) down

down.total: guard-APP_ENV
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) down -v

logs.db:
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) logs -f baseapi_db

shell.db:
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) exec baseapi_db sh

prune:
	$(DOCKER_COMPOSE_PRUNE)

# Code quality
.PHONY: code.format code.lint code.test code.cov code.cov.html code.check
code.format:
	ruff format

code.lint: code.format
	ruff check --exit-non-zero-on-fix
	slotscheck src
	mypy

code.test:
	pytest -v

code.cov:
	coverage run -m pytest
	coverage combine
	coverage report

code.cov.html:
	coverage run -m pytest
	coverage combine
	coverage html

code.check: code.lint code.test

# Project structure visualization
PYCACHE_DEL := scripts/makefile/pycache_del.sh
DISHKA_PLOT_DATA := scripts/dishka/plot_dependencies_data.py

.PHONY: pycache-del tree plot-data
pycache-del:
	@$(PYCACHE_DEL)

# Clean tree
tree: pycache-del
	@tree

# Dishka
plot-data:
	python $(DISHKA_PLOT_DATA)
