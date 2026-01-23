# Makefile for Poker EV Trainer
# Usage: make <target>

.PHONY: help install install-dev test test-unit test-api test-coverage lint run-backend run-frontend run clean

# Default target
help:
	@echo "Poker EV Trainer - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install development dependencies (includes test tools)"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-api      Run API tests only"
	@echo "  make test-coverage Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  make run-backend   Start backend server"
	@echo "  make run-frontend  Start frontend dev server"
	@echo "  make run           Start both backend and frontend"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         Remove build artifacts and caches"

# Installation
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

install-dev:
	cd backend && pip install -r requirements-dev.txt
	cd frontend && npm install

# Testing (these don't deploy to prod - only run locally)
test:
	cd backend && python run_tests.py

test-unit:
	cd backend && python run_tests.py --unit

test-api:
	cd backend && python run_tests.py --api

test-coverage:
	cd backend && python run_tests.py --coverage

# Development servers
run-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

run:
	@echo "Starting backend and frontend..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@make -j2 run-backend run-frontend

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	@echo "Cleaned!"

