install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Starting development environment..."
	./scripts/dev.sh

build:
	@echo "Building Docker images..."
	docker-compose build

test:
	@echo "Running tests..."
	pytest
	cd frontend && npm test

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

clean:
	@echo "Cleaning up..."
	docker-compose down --volumes --remove-orphans
	rm -rf backend/__pycache__ frontend/.next