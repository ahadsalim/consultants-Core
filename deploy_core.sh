#!/usr/bin/env bash

# Core-System Deployment Script
# Automated deployment for Windows 11 + WSL2

set -e

echo "🚀 Core-System Deployment Starting..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if port is in use
check_port() {
    local port=$1
    local service=$2
    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        print_warning "Port $port is in use (needed for $service)"
        return 1
    fi
    return 0
}

# Function to kill process using port
kill_port_process() {
    local port=$1
    local service=$2
    print_info "Attempting to free port $port for $service..."
    
    # Try to find and kill process using the port
    local pid=$(lsof -ti:$port 2>/dev/null || netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | head -1)
    
    if [ ! -z "$pid" ] && [ "$pid" != "-" ]; then
        print_info "Killing process $pid using port $port"
        kill -9 $pid 2>/dev/null || sudo kill -9 $pid 2>/dev/null || true
        sleep 2
    fi
}

# Function to retry with backoff
retry_with_backoff() {
    local max_attempts=$1
    local delay=$2
    local command="${@:3}"
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$command"; then
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            return 1
        fi
        
        print_info "Attempt $attempt failed, retrying in ${delay}s..."
        sleep $delay
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done
}

# Check if Docker is running
print_info "Checking Docker availability..."
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
print_status "Docker Compose is available ($COMPOSE_CMD)"

# Setup environment file
if [ ! -f .env ]; then
    print_info "Creating environment file..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status "Environment file created from .env.example"
        print_warning "Please review and update .env with your configuration"
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_status "Environment file exists"
fi

# Stop existing containers first
print_info "Stopping existing containers..."
$COMPOSE_CMD -f docker-compose.core.yml down --remove-orphans 2>/dev/null || true
print_status "Existing containers stopped"

# Wait a moment for ports to be released
sleep 3

# Check and handle port conflicts
print_info "Checking port availability..."
PORTS_TO_CHECK=(
    "5432:PostgreSQL"
    "8000:Core API"
    "8082:Adminer"
    "9000:MinIO API"
    "9001:MinIO Console"
)

CONFLICTS_FOUND=false
for port_service in "${PORTS_TO_CHECK[@]}"; do
    port=$(echo $port_service | cut -d':' -f1)
    service=$(echo $port_service | cut -d':' -f2)
    
    if ! check_port $port "$service"; then
        CONFLICTS_FOUND=true
        kill_port_process $port "$service"
    fi
done

# Double-check ports after cleanup
if [ "$CONFLICTS_FOUND" = true ]; then
    print_info "Rechecking ports after cleanup..."
    sleep 2
    for port_service in "${PORTS_TO_CHECK[@]}"; do
        port=$(echo $port_service | cut -d':' -f1)
        service=$(echo $port_service | cut -d':' -f2)
        
        if ! check_port $port "$service"; then
            print_error "Port $port is still in use after cleanup. Please manually stop the service using this port."
            print_info "You can try: sudo lsof -ti:$port | xargs sudo kill -9"
            exit 1
        fi
    done
fi

print_status "All required ports are available"

# Create or recreate network
print_info "Setting up Docker network..."
if docker network ls | grep -q advisor_net; then
    print_info "Removing existing advisor_net network..."
    docker network rm advisor_net 2>/dev/null || true
fi

if ! retry_with_backoff 3 2 "docker network create advisor_net"; then
    print_error "Failed to create Docker network after multiple attempts"
    exit 1
fi
print_status "Docker network 'advisor_net' created"

# Build and start services with retry
print_info "Building and starting services..."
if ! retry_with_backoff 3 5 "$COMPOSE_CMD -f docker-compose.core.yml up -d --build"; then
    print_error "Failed to start services after multiple attempts"
    print_info "Checking container logs for errors..."
    $COMPOSE_CMD -f docker-compose.core.yml logs --tail=20
    exit 1
fi

print_status "Services started successfully"

# Wait for services to be ready with health checks
print_info "Waiting for services to be ready..."
print_info "Database readiness is handled by prestart.sh"

# Wait for API to be healthy
print_info "Checking API health..."
API_READY=false
for i in {1..30}; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        API_READY=true
        break
    fi
    if [ $((i % 5)) -eq 0 ]; then
        print_info "Still waiting for API... (attempt $i/30)"
    fi
    sleep 2
done

if [ "$API_READY" = false ]; then
    print_error "API failed to become healthy"
    print_info "Checking API container logs..."
    $COMPOSE_CMD -f docker-compose.core.yml logs core_api --tail=20
    exit 1
fi

print_status "API is healthy and responding"

# Validate deployment
print_info "Validating deployment..."
if [ -f scripts/validate_deployment.py ]; then
    python3 scripts/validate_deployment.py
else
    # Extended validation
    print_info "Running basic validation checks..."
    
    # Check database connection
    if docker exec core_db pg_isready -U postgres > /dev/null 2>&1; then
        print_status "Database is ready"
    else
        print_error "Database is not ready"
        exit 1
    fi
    
    # Check MinIO
    if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        print_status "MinIO is ready"
    else
        print_warning "MinIO health check failed (this might be normal)"
    fi
    
    # Check API endpoints
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_status "API health endpoint working"
    else
        print_error "API health endpoint failed"
        exit 1
    fi
fi

echo ""
echo "🎉 Core-System Deployment Complete!"
echo "===================================="
echo ""
echo "📋 Access URLs:"
echo "  • API Health:    http://localhost:8000/health"
echo "  • API Docs:      http://localhost:8000/docs"
echo "  • API Stats:     http://localhost:8000/stats"
echo "  • Sync Status:   http://localhost:8000/sync/status"
echo "  • Database:      http://localhost:8082"
echo "  • MinIO Console: http://localhost:9001"
echo ""
echo "🔧 Useful Commands:"
echo "  • View logs:     $COMPOSE_CMD -f docker-compose.core.yml logs -f"
echo "  • Stop services: $COMPOSE_CMD -f docker-compose.core.yml down"
echo "  • Restart API:   $COMPOSE_CMD -f docker-compose.core.yml restart core_api"
echo "  • Run tests:     docker exec -it core_api pytest"
echo "  • DB shell:      docker exec -it core_db psql -U postgres -d coredb"
echo ""
echo "🔍 Troubleshooting:"
echo "  • Check logs:    $COMPOSE_CMD -f docker-compose.core.yml logs [service_name]"
echo "  • Port conflicts: sudo lsof -i :[port_number]"
echo "  • Reset all:     $COMPOSE_CMD -f docker-compose.core.yml down -v && docker system prune -f"
echo ""
echo "📖 For more information, see README.md"
