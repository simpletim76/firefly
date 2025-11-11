.PHONY: help build up down restart logs clean test setup

help:
	@echo "Project Firefly - Makefile Commands"
	@echo "===================================="
	@echo "make build    - Build Docker image"
	@echo "make up       - Start container"
	@echo "make down     - Stop container"
	@echo "make restart  - Restart container"
	@echo "make logs     - View container logs"
	@echo "make clean    - Clean up containers and volumes"
	@echo "make test     - Run tests"
	@echo "make setup    - Run setup script"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Firefly is starting..."
	@echo "Web interface: http://localhost:8080"
	@echo "Default login: admin / admin123"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	rm -rf data/*.db logs/*.log

test:
	python3 -m pytest tests/ -v

setup:
	python3 setup.py

status:
	docker-compose ps
