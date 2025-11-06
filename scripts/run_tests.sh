#!/bin/bash

# Test runner script for the Multi-Agent Ticket Management System
# This script provides convenient commands for running tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  Multi-Agent System Test Runner${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo -e "${YELLOW}Install with: pip install pytest pytest-cov pytest-mock${NC}"
    exit 1
fi

# Function to run tests
run_tests() {
    local test_path=$1
    local description=$2

    echo -e "${YELLOW}Running: ${description}${NC}"
    echo "----------------------------------------"
    pytest "$test_path" -v
    echo ""
}

# Parse command line arguments
case "${1:-all}" in
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest tests/ -v --cov=src --cov-report=term-missing
        ;;

    intake)
        run_tests "tests/test_intake_agent.py" "Intake Agent Tests"
        ;;

    faq)
        run_tests "tests/test_faq_agent.py" "FAQ Lookup Agent Tests"
        ;;

    classifier)
        run_tests "tests/test_classifier_agent.py" "Classifier Agent Tests"
        ;;

    technical)
        run_tests "tests/test_technical_agent.py" "Technical Support Agent Tests"
        ;;

    billing)
        run_tests "tests/test_billing_agent.py" "Billing Support Agent Tests"
        ;;

    general)
        run_tests "tests/test_general_agent.py" "General Support Agent Tests"
        ;;

    escalation)
        run_tests "tests/test_escalation_agent.py" "Escalation Agent Tests"
        ;;

    response)
        run_tests "tests/test_response_agent.py" "Response Generator Agent Tests"
        ;;

    coverage)
        echo -e "${GREEN}Running tests with coverage report...${NC}"
        pytest tests/ -v --cov=src --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;

    quick)
        echo -e "${GREEN}Running quick test (no coverage)...${NC}"
        pytest tests/ -v
        ;;

    failed)
        echo -e "${GREEN}Re-running failed tests...${NC}"
        pytest tests/ -v --lf
        ;;

    watch)
        echo -e "${GREEN}Running tests in watch mode...${NC}"
        echo -e "${YELLOW}Note: Requires pytest-watch (install with: pip install pytest-watch)${NC}"
        ptw tests/ -- -v
        ;;

    help)
        echo "Usage: ./run_tests.sh [command]"
        echo ""
        echo "Commands:"
        echo "  all           - Run all tests with coverage (default)"
        echo "  quick         - Run all tests without coverage"
        echo "  coverage      - Run tests and generate HTML coverage report"
        echo "  failed        - Re-run only failed tests"
        echo ""
        echo "Individual Agent Tests:"
        echo "  intake        - Run Intake Agent tests"
        echo "  faq           - Run FAQ Lookup Agent tests"
        echo "  classifier    - Run Classifier Agent tests"
        echo "  technical     - Run Technical Support Agent tests"
        echo "  billing       - Run Billing Support Agent tests"
        echo "  general       - Run General Support Agent tests"
        echo "  escalation    - Run Escalation Agent tests"
        echo "  response      - Run Response Generator Agent tests"
        echo ""
        echo "Other:"
        echo "  watch         - Run tests in watch mode (requires pytest-watch)"
        echo "  help          - Show this help message"
        ;;

    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

# Exit with success
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  Tests completed!${NC}"
echo -e "${GREEN}=====================================${NC}"
