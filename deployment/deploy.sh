#!/bin/bash

# Mobile PlantGuard Deployment Script
# This script handles deployment of the mobile-optimized PlantGuard application

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
DOCKER_COMPOSE_FILE="docker-compose.mobile.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to validate configuration
validate_config() {
    log_info "Validating configuration..."
    
    # Check if required files exist
    local required_files=(
        "$SCRIPT_DIR/$DOCKER_COMPOSE_FILE"
        "$SCRIPT_DIR/Dockerfile.mobile"
        "$SCRIPT_DIR/mobile_deployment_config.yaml"
        "$PROJECT_ROOT/mobile_plantguard_app.py"
        "$PROJECT_ROOT/requirements.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    # Check if model files exist
    if [[ ! -d "$PROJECT_ROOT/data/models" ]]; then
        log_warning "Model directory not found. Models will be downloaded on first run."
    fi
    
    log_success "Configuration validation passed"
}

# Function to prepare environment
prepare_environment() {
    log_info "Preparing deployment environment..."
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data/models"
    mkdir -p "$PROJECT_ROOT/temp"
    
    # Set proper permissions
    chmod 755 "$PROJECT_ROOT/logs"
    chmod 755 "$PROJECT_ROOT/data/models"
    chmod 755 "$PROJECT_ROOT/temp"
    
    # Copy deployment configuration
    cp "$SCRIPT_DIR/mobile_deployment_config.yaml" "$PROJECT_ROOT/config/"
    
    log_success "Environment preparation completed"
}

# Function to build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$SCRIPT_DIR"
    
    # Build mobile application image
    docker-compose -f "$DOCKER_COMPOSE_FILE" build plantguard-mobile
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        exit 1
    fi
}

# Function to start services
start_services() {
    log_info "Starting services..."
    
    cd "$SCRIPT_DIR"
    
    # Start services based on environment
    if [[ "$DEPLOYMENT_ENV" == "development" ]]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" --profile development up -d
    else
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Services started successfully"
    else
        log_error "Failed to start services"
        exit 1
    fi
}

# Function to wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost:8501/health > /dev/null 2>&1; then
            log_success "Services are ready"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Services not ready yet, waiting..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Services failed to become ready within expected time"
    return 1
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check main application
    if curl -f -s http://localhost:8501/health > /dev/null; then
        log_success "Main application health check passed"
    else
        log_error "Main application health check failed"
        return 1
    fi
    
    # Check if containers are running
    local containers=("plantguard-mobile" "plantguard-nginx-mobile")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            log_success "Container $container is running"
        else
            log_warning "Container $container is not running"
        fi
    done
    
    return 0
}

# Function to display deployment information
show_deployment_info() {
    log_info "Deployment Information:"
    echo "=========================="
    echo "Environment: $DEPLOYMENT_ENV"
    echo "Application URL: http://localhost:8501"
    echo "Health Check: http://localhost:8501/health"
    echo "Logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "Stop: docker-compose -f $DOCKER_COMPOSE_FILE down"
    echo "=========================="
}

# Function to cleanup on failure
cleanup_on_failure() {
    log_warning "Cleaning up due to deployment failure..."
    cd "$SCRIPT_DIR"
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    log_info "Cleanup completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENVIRONMENT    Set deployment environment (development|production)"
    echo "  -h, --help              Show this help message"
    echo "  --build-only            Only build images, don't start services"
    echo "  --no-health-check       Skip health checks"
    echo ""
    echo "Environment Variables:"
    echo "  DEPLOYMENT_ENV          Deployment environment (default: production)"
    echo ""
    echo "Examples:"
    echo "  $0                      Deploy in production mode"
    echo "  $0 -e development       Deploy in development mode"
    echo "  $0 --build-only         Only build Docker images"
}

# Parse command line arguments
BUILD_ONLY=false
SKIP_HEALTH_CHECK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            DEPLOYMENT_ENV="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --no-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$DEPLOYMENT_ENV" != "development" && "$DEPLOYMENT_ENV" != "production" ]]; then
    log_error "Invalid environment: $DEPLOYMENT_ENV. Must be 'development' or 'production'"
    exit 1
fi

# Main deployment process
main() {
    log_info "Starting Mobile PlantGuard deployment..."
    log_info "Environment: $DEPLOYMENT_ENV"
    
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    # Run deployment steps
    check_prerequisites
    validate_config
    prepare_environment
    build_images
    
    if [[ "$BUILD_ONLY" == "true" ]]; then
        log_success "Build completed successfully"
        exit 0
    fi
    
    start_services
    wait_for_services
    
    if [[ "$SKIP_HEALTH_CHECK" != "true" ]]; then
        run_health_checks
    fi
    
    show_deployment_info
    log_success "Mobile PlantGuard deployment completed successfully!"
}

# Run main function
main "$@"