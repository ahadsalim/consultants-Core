#!/bin/bash

# Core-System Deployment Script
# Automated deployment for Windows 11 + WSL2

set -e

echo "🚀 Core-System Deployment Starting..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

print_status "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

print_status "Docker Compose is available"

# Create network if it doesn't exist
if ! docker network ls | grep -q advisor_net; then
    echo "📡 Creating advisor_net network..."
    docker network create advisor_net
    print_status "Network created"
else
    print_status "Network advisor_net already exists"
fi

# Setup environment file
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    print_status "Environment file created from .env.example"
    print_warning "Please review and update .env with your configuration"
else
    print_status "Environment file exists"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
$COMPOSE_CMD -f docker-compose.core.yml down

# Build and start services
echo "🏗️  Building and starting services..."
$COMPOSE_CMD -f docker-compose.core.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Validate deployment
echo "🔍 Validating deployment..."
if [ -f scripts/validate_deployment.py ]; then
    python3 scripts/validate_deployment.py
else
    # Basic validation
    echo "📡 Checking API health..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            print_status "API is responding"
            break
        fi
        if [ $i -eq 10 ]; then
            print_error "API failed to start"
            exit 1
        fi
        sleep 3
    done
fi

echo ""
echo "🎉 Core-System Deployment Complete!"
echo "===================================="
echo ""
echo "📋 Access URLs:"
echo "  • API Health:    http://localhost:8000/health"
echo "  • API Docs:      http://localhost:8000/docs"
echo "  • API Stats:     http://localhost:8000/stats"
echo "  • Database:      http://localhost:8082"
echo "  • MinIO Console: http://localhost:9001"
echo ""
echo "🔧 Useful Commands:"
echo "  • View logs:     $COMPOSE_CMD -f docker-compose.core.yml logs -f"
echo "  • Stop services: $COMPOSE_CMD -f docker-compose.core.yml down"
echo "  • Run tests:     docker exec -it core_api pytest"
echo "  • DB shell:      docker exec -it core_db psql -U postgres -d coredb"
echo ""
echo "📖 For more information, see README.md"
