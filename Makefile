.PHONY: help build up down restart logs clean test migrate shell db-shell

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - View logs from all services"
	@echo "  clean     - Remove all containers and volumes"
	@echo "  test      - Run tests"
	@echo "  migrate   - Run database migrations"
	@echo "  shell     - Access API container shell"
	@echo "  db-shell  - Access database shell"
	@echo "  network   - Create advisor_net network"

# Create Docker network
network:
	@docker network create advisor_net || echo "Network already exists"

# Build Docker images
build:
	docker compose -f docker-compose.core.yml build

# Start services
up: network
	docker compose -f docker-compose.core.yml up -d

# Stop services
down:
	docker compose -f docker-compose.core.yml down

# Restart services
restart: down up

# View logs
logs:
	docker compose -f docker-compose.core.yml logs -f

# Clean up everything
clean:
	docker compose -f docker-compose.core.yml down -v --remove-orphans
	docker system prune -f

# Run tests
test:
	docker exec -it core_api pytest tests/ -v

# Run database migrations
migrate:
	docker exec -it core_api alembic upgrade head

# Generate new migration
migration:
	@read -p "Enter migration message: " msg; \
	docker exec -it core_api alembic revision --autogenerate -m "$$msg"

# Access API container shell
shell:
	docker exec -it core_api /bin/bash

# Access database shell
db-shell:
	docker exec -it core_db psql -U postgres -d coredb

# View service status
status:
	docker compose -f docker-compose.core.yml ps

# Setup environment
setup: network
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env with your configuration"; \
	fi

# Full deployment
deploy: setup build up migrate
	@echo "Deployment complete!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Adminer: http://localhost:8082"
	@echo "MinIO: http://localhost:9001"

# Development setup
dev: setup up
	@echo "Development environment ready!"
	@echo "API: http://localhost:8000"
	@echo "Health: http://localhost:8000/health"
