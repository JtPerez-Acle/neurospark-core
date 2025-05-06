#!/bin/bash
# Deploy NeuroSpark Core to the specified environment

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
VERSION=$(git describe --tags --always)
SKIP_TESTS=false
SKIP_BUILD=false
DRY_RUN=false

# Function to print section header
print_section() {
    echo -e "\n${YELLOW}==== $1 ====${NC}\n"
}

# Function to print usage
print_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -e, --environment <env>  Deployment environment (development, staging, production)"
    echo "  -v, --version <version>  Version to deploy (default: git describe)"
    echo "  -s, --skip-tests         Skip running tests"
    echo "  -b, --skip-build         Skip building Docker images"
    echo "  -d, --dry-run            Dry run (don't actually deploy)"
    echo "  -h, --help               Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -b|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo -e "${RED}Invalid environment: $ENVIRONMENT${NC}"
    echo "Valid environments: development, staging, production"
    exit 1
fi

# Main function
main() {
    print_section "Starting deployment to $ENVIRONMENT environment"
    echo "Version: $VERSION"
    echo "Skip tests: $SKIP_TESTS"
    echo "Skip build: $SKIP_BUILD"
    echo "Dry run: $DRY_RUN"
    
    # Run tests if not skipped
    if [[ "$SKIP_TESTS" == "false" ]]; then
        print_section "Running tests"
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "Would run: ./scripts/run_ci.sh"
        else
            ./scripts/run_ci.sh || { echo -e "${RED}Tests failed${NC}"; exit 1; }
        fi
    fi
    
    # Build Docker images if not skipped
    if [[ "$SKIP_BUILD" == "false" ]]; then
        print_section "Building Docker images"
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "Would build Docker images with tag: $VERSION"
        else
            # Build Docker images
            local services=("base" "api" "curator" "vectoriser" "professor" "reviewer" "tutor" "auditor" "custodian" "governor")
            for service in "${services[@]}"; do
                echo "Building $service image..."
                docker build -t "neurospark-$service:$VERSION" -f "docker/Dockerfile.$service" . || { echo -e "${RED}Docker build for $service failed${NC}"; exit 1; }
                echo -e "${GREEN}Docker build for $service successful${NC}"
            done
        fi
    fi
    
    # Deploy to the specified environment
    print_section "Deploying to $ENVIRONMENT"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would deploy version $VERSION to $ENVIRONMENT"
    else
        # Set environment variables
        export ENVIRONMENT="$ENVIRONMENT"
        export VERSION="$VERSION"
        
        # Deploy using Docker Compose
        echo "Deploying with Docker Compose..."
        docker-compose -f docker-compose.yml -f "docker-compose.$ENVIRONMENT.yml" up -d || { echo -e "${RED}Deployment failed${NC}"; exit 1; }
        
        # Run database migrations
        echo "Running database migrations..."
        docker-compose exec api alembic upgrade head || { echo -e "${RED}Database migrations failed${NC}"; exit 1; }
        
        echo -e "${GREEN}Deployment successful${NC}"
    fi
    
    print_section "Deployment completed"
}

# Run main function
main
