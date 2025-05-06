#!/bin/bash
# Rollback NeuroSpark Core to a previous version

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
VERSION=""
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
    echo "  -v, --version <version>  Version to rollback to (required)"
    echo "  -d, --dry-run            Dry run (don't actually rollback)"
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

# Validate version
if [[ -z "$VERSION" ]]; then
    echo -e "${RED}Version is required${NC}"
    print_usage
    exit 1
fi

# Main function
main() {
    print_section "Starting rollback to version $VERSION in $ENVIRONMENT environment"
    echo "Dry run: $DRY_RUN"
    
    # Check if the version exists
    if [[ "$DRY_RUN" == "false" ]]; then
        local services=("base" "api" "curator" "vectoriser" "professor" "reviewer" "tutor" "auditor" "custodian" "governor")
        for service in "${services[@]}"; do
            if ! docker image inspect "neurospark-$service:$VERSION" &>/dev/null; then
                echo -e "${RED}Image neurospark-$service:$VERSION does not exist${NC}"
                echo "You may need to pull it from the registry first"
                exit 1
            fi
        done
    fi
    
    # Rollback to the specified version
    print_section "Rolling back to version $VERSION in $ENVIRONMENT"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would rollback to version $VERSION in $ENVIRONMENT"
    else
        # Set environment variables
        export ENVIRONMENT="$ENVIRONMENT"
        export VERSION="$VERSION"
        
        # Stop the current deployment
        echo "Stopping current deployment..."
        docker-compose -f docker-compose.yml -f "docker-compose.$ENVIRONMENT.yml" down || { echo -e "${RED}Failed to stop current deployment${NC}"; exit 1; }
        
        # Deploy the specified version
        echo "Deploying version $VERSION..."
        docker-compose -f docker-compose.yml -f "docker-compose.$ENVIRONMENT.yml" up -d || { echo -e "${RED}Rollback failed${NC}"; exit 1; }
        
        # Rollback database migrations if needed
        echo "Rolling back database migrations..."
        docker-compose exec api alembic downgrade -1 || { echo -e "${RED}Database rollback failed${NC}"; exit 1; }
        
        echo -e "${GREEN}Rollback successful${NC}"
    fi
    
    print_section "Rollback completed"
}

# Run main function
main
