# Makefile for Wild Ginger Bot Docker Operations

.PHONY: help build run stop logs clean dev prod test shell backup restore

# Default target
help:
	@echo "Wild Ginger Bot Docker Operations"
	@echo "=================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-build    - Build and start development environment"
	@echo "  make dev-logs     - Show development logs"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build and start production environment"
	@echo "  make prod-logs    - Show production logs"
	@echo ""
	@echo "General:"
	@echo "  make build        - Build Docker image"
	@echo "  make stop         - Stop all containers"
	@echo "  make logs         - Show logs"
	@echo "  make clean        - Remove containers and images"
	@echo "  make shell        - Open shell in running container"
	@echo "  make test         - Run tests in container"
	@echo "  make backup       - Backup logs and data"
	@echo "  make restore      - Restore from backup"
	@echo "  make setup        - Initial setup (create directories, copy env)"

# Initial setup
setup:
	@echo "Setting up Wild Ginger Bot..."
	@mkdir -p credentials logs
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp docker.env.example .env; \
		echo "Please edit .env with your actual configuration values"; \
	else \
		echo ".env file already exists"; \
	fi
	@echo "Setup complete! Please ensure you have:"
	@echo "1. Google Sheets credentials in credentials/credentials.json"
	@echo "2. Proper configuration in .env file"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker-compose build

# Development environment
dev:
	@echo "Starting development environment..."
	docker-compose up

dev-build:
	@echo "Building and starting development environment..."
	docker-compose up --build

dev-logs:
	@echo "Showing development logs..."
	docker-compose logs -f

# Production environment
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build:
	@echo "Building and starting production environment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-logs:
	@echo "Showing production logs..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# General operations
stop:
	@echo "Stopping all containers..."
	docker-compose down

logs:
	@echo "Showing logs..."
	docker-compose logs -f

shell:
	@echo "Opening shell in container..."
	docker-compose exec wild-ginger-bot /bin/bash

test:
	@echo "Running tests..."
	docker-compose exec wild-ginger-bot python -m pytest

# Cleanup
clean:
	@echo "Cleaning up containers and images..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

# Backup and restore
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='backups' \
		--exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.pytest_cache' \
		--exclude='htmlcov' \
		--exclude='.coverage' \
		.
	@echo "Backup created in backups/"

restore:
	@echo "Available backups:"
	@ls -la backups/ 2>/dev/null || echo "No backups found"
	@echo ""
	@echo "To restore, run: tar -xzf backups/backup-YYYYMMDD-HHMMSS.tar.gz"

# Health check
health:
	@echo "Checking container health..."
	@docker-compose ps
	@echo ""
	@echo "Health status:"
	@docker-compose exec wild-ginger-bot python -c "import sys; print('Container is healthy')" 2>/dev/null || echo "Container is unhealthy"

# Monitor resources
monitor:
	@echo "Monitoring resource usage..."
	docker stats wild-ginger-bot

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	docker-compose exec wild-ginger-bot pip install --upgrade -r requirements.txt

# Database operations (if needed)
db-backup:
	@echo "Backing up database..."
	@mkdir -p backups/db
	@tar -czf backups/db/db-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/

db-restore:
	@echo "Available database backups:"
	@ls -la backups/db/ 2>/dev/null || echo "No database backups found"

# Security check
security-check:
	@echo "Running security checks..."
	@echo "1. Checking file permissions..."
	@ls -la credentials/ 2>/dev/null || echo "No credentials directory found"
	@echo ""
	@echo "2. Checking for sensitive files in git..."
	@git ls-files | grep -E '\.(key|pem|p12|json|env)$' || echo "No sensitive files found in git"
	@echo ""
	@echo "3. Checking container user..."
	@docker-compose exec wild-ginger-bot whoami 2>/dev/null || echo "Container not running"

# Quick restart
restart:
	@echo "Restarting services..."
	docker-compose restart

# View configuration
config:
	@echo "Current Docker Compose configuration:"
	docker-compose config

# Development helpers
dev-debug:
	@echo "Starting development with debug mode..."
	@echo "Uncomment debug command in docker-compose.override.yml first"
	docker-compose up --build

dev-test:
	@echo "Running tests in development environment..."
	docker-compose exec wild-ginger-bot python -m pytest -v

# Production helpers
prod-deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "Production deployment complete"

prod-update:
	@echo "Updating production deployment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "Production update complete" 