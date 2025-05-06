#!/bin/bash
# Run CI pipeline locally

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
    
    if ! command_exists flake8; then
        missing_tools+=("flake8")
    fi
    
    if ! command_exists black; then
        missing_tools+=("black")
    fi
    
    if ! command_exists isort; then
        missing_tools+=("isort")
    fi
    
    if ! command_exists mypy; then
        missing_tools+=("mypy")
    fi
    
    if ! command_exists pytest; then
        missing_tools+=("pytest")
    fi
    
    if ! command_exists bandit; then
        missing_tools+=("bandit")
    fi
    
    if ! command_exists safety; then
        missing_tools+=("safety")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo -e "${RED}The following tools are missing:${NC}"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo -e "\nPlease install them with:"
        echo -e "  pip install -e \".[dev]\""
        exit 1
    fi
    
    echo -e "${GREEN}All required tools are installed.${NC}"
}

# Run linting
run_linting() {
    print_section "Running linting"
    
    echo "Running flake8..."
    flake8 src tests || { echo -e "${RED}Flake8 failed${NC}"; exit 1; }
    echo -e "${GREEN}Flake8 passed${NC}"
    
    echo "Running black..."
    black --check src tests || { echo -e "${RED}Black failed${NC}"; exit 1; }
    echo -e "${GREEN}Black passed${NC}"
    
    echo "Running isort..."
    isort --check-only --profile black src tests || { echo -e "${RED}isort failed${NC}"; exit 1; }
    echo -e "${GREEN}isort passed${NC}"
    
    echo "Running mypy..."
    mypy src || { echo -e "${RED}mypy failed${NC}"; exit 1; }
    echo -e "${GREEN}mypy passed${NC}"
}

# Run tests
run_tests() {
    print_section "Running tests"
    
    echo "Running unit tests..."
    pytest -v tests/ -m "unit or not marked" --cov=src --cov-report=term || { echo -e "${RED}Unit tests failed${NC}"; exit 1; }
    echo -e "${GREEN}Unit tests passed${NC}"
    
    echo "Running integration tests..."
    pytest -v tests/ -m "integration" --cov=src --cov-report=term --cov-append || { echo -e "${RED}Integration tests failed${NC}"; exit 1; }
    echo -e "${GREEN}Integration tests passed${NC}"
    
    echo "Running end-to-end tests..."
    pytest -v tests/ -m "e2e" --cov=src --cov-report=term --cov-append || { echo -e "${RED}End-to-end tests failed${NC}"; exit 1; }
    echo -e "${GREEN}End-to-end tests passed${NC}"
    
    echo "Generating coverage report..."
    pytest --cov=src --cov-report=xml tests/ || { echo -e "${RED}Coverage report generation failed${NC}"; exit 1; }
    echo -e "${GREEN}Coverage report generated${NC}"
}

# Run security checks
run_security_checks() {
    print_section "Running security checks"
    
    echo "Running bandit..."
    bandit -r src -f json -o bandit-results.json || { echo -e "${RED}Bandit failed${NC}"; exit 1; }
    echo -e "${GREEN}Bandit passed${NC}"
    
    echo "Running safety..."
    safety check || { echo -e "${RED}Safety check failed${NC}"; exit 1; }
    echo -e "${GREEN}Safety check passed${NC}"
}

# Main function
main() {
    print_section "Starting CI pipeline"
    
    check_requirements
    run_linting
    run_tests
    run_security_checks
    
    print_section "CI pipeline completed successfully"
}

# Run main function
main
