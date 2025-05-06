#!/bin/bash
# Run CD pipeline locally

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print section header
print_section() {
    echo -e "\n${YELLOW}==== $1 ====${NC}\n"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required tools are installed
check_requirements() {
    print_section "Checking requirements"
    
    local missing_tools=()
    
    if ! command_exists python; then
        missing_tools+=("python")
    fi
    
    if ! command_exists pip; then
        missing_tools+=("pip")
    fi
    
    if ! command_exists docker; then
        missing_tools+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_tools+=("docker-compose")
    fi
    
    if ! command_exists build; then
        missing_tools+=("build")
    fi
    
    if ! command_exists twine; then
        missing_tools+=("twine")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo -e "${RED}The following tools are missing:${NC}"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo -e "\nPlease install them with:"
        echo -e "  pip install build twine"
        exit 1
    fi
    
    echo -e "${GREEN}All required tools are installed.${NC}"
}

# Build package
build_package() {
    print_section "Building package"
    
    echo "Building package..."
    python -m build || { echo -e "${RED}Build failed${NC}"; exit 1; }
    echo -e "${GREEN}Build successful${NC}"
    
    echo "Checking package..."
    twine check dist/* || { echo -e "${RED}Package check failed${NC}"; exit 1; }
    echo -e "${GREEN}Package check passed${NC}"
}

# Build Docker images
build_docker_images() {
    print_section "Building Docker images"
    
    local services=("base" "api" "curator" "vectoriser" "professor" "reviewer" "tutor" "auditor" "custodian" "governor")
    
    for service in "${services[@]}"; do
        echo "Building $service image..."
        docker build -t "neurospark-$service:local" -f "docker/Dockerfile.$service" . || { echo -e "${RED}Docker build for $service failed${NC}"; exit 1; }
        echo -e "${GREEN}Docker build for $service successful${NC}"
    done
}

# Test Docker Compose
test_docker_compose() {
    print_section "Testing Docker Compose"
    
    echo "Validating docker-compose.yml..."
    docker-compose config || { echo -e "${RED}Docker Compose validation failed${NC}"; exit 1; }
    echo -e "${GREEN}Docker Compose validation successful${NC}"
    
    echo "Starting essential services..."
    docker-compose up -d postgres redis qdrant elasticlite minio || { echo -e "${RED}Docker Compose up failed${NC}"; exit 1; }
    echo -e "${GREEN}Essential services started${NC}"
    
    echo "Waiting for services to be ready..."
    sleep 30
    
    echo "Checking service health..."
    docker-compose ps || { echo -e "${RED}Service health check failed${NC}"; exit 1; }
    echo -e "${GREEN}Service health check passed${NC}"
    
    echo "Stopping services..."
    docker-compose down -v || { echo -e "${RED}Docker Compose down failed${NC}"; exit 1; }
    echo -e "${GREEN}Services stopped${NC}"
}

# Main function
main() {
    print_section "Starting CD pipeline"
    
    check_requirements
    build_package
    build_docker_images
    test_docker_compose
    
    print_section "CD pipeline completed successfully"
}

# Run main function
main
