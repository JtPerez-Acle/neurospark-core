#!/bin/bash
# Run performance tests

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
    
    if ! command_exists pytest; then
        missing_tools+=("pytest")
    fi
    
    if ! command_exists ab; then
        missing_tools+=("ab (Apache Benchmark)")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo -e "${RED}The following tools are missing:${NC}"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo -e "\nPlease install them with:"
        echo -e "  pip install pytest"
        echo -e "  # For ab, install apache2-utils"
        exit 1
    fi
    
    echo -e "${GREEN}All required tools are installed.${NC}"
}

# Run performance tests
run_performance_tests() {
    print_section "Running performance tests"
    
    echo "Running performance tests..."
    pytest -v tests/performance/ -m "performance" || { echo -e "${RED}Performance tests failed${NC}"; exit 1; }
    echo -e "${GREEN}Performance tests passed${NC}"
}

# Run API load tests
run_api_load_tests() {
    print_section "Running API load tests"
    
    # Check if the API is running
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${YELLOW}API is not running, skipping load tests${NC}"
        return
    fi
    
    echo "Running load tests on API..."
    
    # Run Apache Benchmark
    echo "Testing /health endpoint..."
    ab -n 1000 -c 10 http://localhost:8000/health > ab-health-results.txt || { echo -e "${RED}Load test failed${NC}"; exit 1; }
    
    # Extract results
    local requests_per_second=$(grep "Requests per second" ab-health-results.txt | awk '{print $4}')
    local time_per_request=$(grep "Time per request" ab-health-results.txt | head -1 | awk '{print $4}')
    local failed_requests=$(grep "Failed requests" ab-health-results.txt | awk '{print $3}')
    
    echo "Load test results:"
    echo "  - Requests per second: $requests_per_second"
    echo "  - Time per request: $time_per_request ms"
    echo "  - Failed requests: $failed_requests"
    
    if [ "$failed_requests" -gt 0 ]; then
        echo -e "${RED}Failed requests detected!${NC}"
    else
        echo -e "${GREEN}Load test passed${NC}"
    fi
}

# Run database performance tests
run_db_performance_tests() {
    print_section "Running database performance tests"
    
    echo "Running database performance tests..."
    
    # Create a test script
    cat > db_performance_test.py << EOF
import time
import sqlite3
import random
import string

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def run_db_test(num_records=1000):
    # Connect to an in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create a test table
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        email TEXT,
        first_name TEXT,
        last_name TEXT
    )
    ''')
    
    # Insert test data
    start_time = time.time()
    for i in range(num_records):
        cursor.execute(
            "INSERT INTO users (username, email, first_name, last_name) VALUES (?, ?, ?, ?)",
            (
                generate_random_string(),
                f"{generate_random_string()}@example.com",
                generate_random_string(),
                generate_random_string(),
            )
        )
    conn.commit()
    insert_time = time.time() - start_time
    
    # Query test data
    start_time = time.time()
    for i in range(100):
        user_id = random.randint(1, num_records)
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        cursor.fetchone()
    query_time = time.time() - start_time
    
    # Update test data
    start_time = time.time()
    for i in range(100):
        user_id = random.randint(1, num_records)
        cursor.execute(
            "UPDATE users SET first_name = ?, last_name = ? WHERE id = ?",
            (generate_random_string(), generate_random_string(), user_id)
        )
    conn.commit()
    update_time = time.time() - start_time
    
    # Delete test data
    start_time = time.time()
    for i in range(100):
        user_id = random.randint(1, num_records)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    delete_time = time.time() - start_time
    
    # Close the connection
    conn.close()
    
    return {
        "insert_time": insert_time,
        "query_time": query_time,
        "update_time": update_time,
        "delete_time": delete_time,
    }

if __name__ == "__main__":
    results = run_db_test()
    print(f"Insert time: {results['insert_time']:.4f}s")
    print(f"Query time: {results['query_time']:.4f}s")
    print(f"Update time: {results['update_time']:.4f}s")
    print(f"Delete time: {results['delete_time']:.4f}s")
EOF
    
    # Run the test script
    python db_performance_test.py || { echo -e "${RED}Database performance test failed${NC}"; exit 1; }
    
    # Clean up
    rm db_performance_test.py
    
    echo -e "${GREEN}Database performance test completed${NC}"
}

# Main function
main() {
    print_section "Starting performance tests"
    
    check_requirements
    run_performance_tests
    run_api_load_tests
    run_db_performance_tests
    
    print_section "Performance tests completed"
}

# Run main function
main
