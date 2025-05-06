#!/bin/bash
# Run security scans

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
    
    if ! command_exists bandit; then
        missing_tools+=("bandit")
    fi
    
    if ! command_exists safety; then
        missing_tools+=("safety")
    fi
    
    if ! command_exists trivy; then
        missing_tools+=("trivy")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo -e "${RED}The following tools are missing:${NC}"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo -e "\nPlease install them with:"
        echo -e "  pip install bandit safety"
        echo -e "  # For trivy, see https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
        exit 1
    fi
    
    echo -e "${GREEN}All required tools are installed.${NC}"
}

# Run Bandit
run_bandit() {
    print_section "Running Bandit"
    
    echo "Running Bandit on src directory..."
    bandit -r src -f json -o bandit-results.json || { echo -e "${RED}Bandit failed${NC}"; exit 1; }
    echo -e "${GREEN}Bandit scan completed${NC}"
    
    # Count issues by severity
    local high_count=$(grep -o '"issue_severity": "HIGH"' bandit-results.json | wc -l)
    local medium_count=$(grep -o '"issue_severity": "MEDIUM"' bandit-results.json | wc -l)
    local low_count=$(grep -o '"issue_severity": "LOW"' bandit-results.json | wc -l)
    
    echo "Bandit found:"
    echo "  - High severity issues: $high_count"
    echo "  - Medium severity issues: $medium_count"
    echo "  - Low severity issues: $low_count"
    
    if [ $high_count -gt 0 ]; then
        echo -e "${RED}High severity issues found!${NC}"
        grep -A 10 '"issue_severity": "HIGH"' bandit-results.json
    fi
}

# Run Safety
run_safety() {
    print_section "Running Safety"
    
    echo "Checking dependencies for vulnerabilities..."
    safety check --json > safety-results.json || { echo -e "${RED}Safety check failed${NC}"; exit 1; }
    echo -e "${GREEN}Safety check completed${NC}"
    
    # Count vulnerabilities
    local vuln_count=$(grep -o '"vulnerability_id":' safety-results.json | wc -l)
    
    echo "Safety found $vuln_count vulnerabilities"
    
    if [ $vuln_count -gt 0 ]; then
        echo -e "${RED}Vulnerabilities found!${NC}"
        cat safety-results.json
    fi
}

# Run Trivy
run_trivy() {
    print_section "Running Trivy"
    
    echo "Running Trivy filesystem scan..."
    trivy fs --format json --output trivy-results.json . || { echo -e "${RED}Trivy scan failed${NC}"; exit 1; }
    echo -e "${GREEN}Trivy scan completed${NC}"
    
    # Count vulnerabilities by severity
    local critical_count=$(grep -o '"Severity":"CRITICAL"' trivy-results.json | wc -l)
    local high_count=$(grep -o '"Severity":"HIGH"' trivy-results.json | wc -l)
    local medium_count=$(grep -o '"Severity":"MEDIUM"' trivy-results.json | wc -l)
    
    echo "Trivy found:"
    echo "  - Critical vulnerabilities: $critical_count"
    echo "  - High vulnerabilities: $high_count"
    echo "  - Medium vulnerabilities: $medium_count"
    
    if [ $critical_count -gt 0 ]; then
        echo -e "${RED}Critical vulnerabilities found!${NC}"
        grep -A 20 '"Severity":"CRITICAL"' trivy-results.json
    fi
}

# Run security tests
run_security_tests() {
    print_section "Running security tests"
    
    echo "Running security tests..."
    pytest -v tests/security/ -m "security" || { echo -e "${RED}Security tests failed${NC}"; exit 1; }
    echo -e "${GREEN}Security tests passed${NC}"
}

# Main function
main() {
    print_section "Starting security scan"
    
    check_requirements
    run_bandit
    run_safety
    run_trivy
    run_security_tests
    
    print_section "Security scan completed"
}

# Run main function
main
