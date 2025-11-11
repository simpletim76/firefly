.PHONY: help build up down restart logs clean test setup prepare

# Detect Docker Compose command (V1 or V2)
DOCKER_COMPOSE := $(shell docker compose version > /dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

help:
	@echo "Project Firefly - Makefile Commands"
	@echo "===================================="
	@echo "make prepare  - Prepare directories with correct permissions"
	@echo "make build    - Build Docker image"
	@echo "make up       - Start container"
	@echo "make down     - Stop container"
	@echo "make restart  - Restart container"
	@echo "make logs     - View container logs"
	@echo "make clean    - Clean up containers and volumes"
	@echo "make test     - Run tests"
	@echo "make setup    - Run setup script"

prepare:
	@echo "Preparing directories..."
	@mkdir -p data logs
	@chmod 777 data logs
	@echo "✓ Directories created with correct permissions"

build: prepare
	$(DOCKER_COMPOSE) build

up: prepare
	$(DOCKER_COMPOSE) up -d
	@echo "Firefly is starting..."
	@echo "Web interface: http://localhost:8080"
	@echo "Default login: admin / admin123"

down:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

logs:
	$(DOCKER_COMPOSE) logs -f

clean:
	$(DOCKER_COMPOSE) down -v
	rm -rf data/*.db logs/*.log

test:
	python3 -m pytest tests/ -v

setup:
	python3 setup.py

status:
	$(DOCKER_COMPOSE) ps
