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
	. env/bin/activate && PYTHONPATH=src python3.12 -m uvicorn app.run:make_app --factory --port 8000 --reload

# Celery
.PHONY: celery celery.worker celery.beat celery.flower
celery: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker -B --loglevel=INFO

celery.worker: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app worker --loglevel=INFO

celery.beat: venv
	PYTHONPATH=src ./env/bin/celery -A app.infrastructure.celery.app.celery_app beat --loglevel=INFO

celery.flower: venv
	PYTHONPATH=src ./env/bin/flower --broker=redis://localhost:6379/0 --port=5555

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
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up -d web_app_db_pg --build

up.db-echo: guard-APP_ENV
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up web_app_db_pg --build

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
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) logs -f web_app_db_pg

shell.db:
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) exec web_app_db_pg sh

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
