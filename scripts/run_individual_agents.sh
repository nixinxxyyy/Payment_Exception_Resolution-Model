#!/bin/bash

# Individual Agent Runner
# Provides convenient commands to test each agent independently

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  Individual Agent Runner${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY not set${NC}"
    echo -e "${YELLOW}Set it with: export OPENAI_API_KEY=sk-your-key-here${NC}"
    exit 1
fi

# Parse command
AGENT=${1:-}
QUERY=${2:-"Test query"}

case "$AGENT" in
    intake)
        echo -e "${BLUE}Testing Intake Agent${NC}"
        python scripts/test_agent_standalone.py intake "$QUERY"
        ;;

    faq)
        echo -e "${BLUE}Testing FAQ Lookup Agent${NC}"
        python scripts/test_agent_standalone.py faq "$QUERY"
        ;;

    classifier)
        echo -e "${BLUE}Testing Classifier Agent${NC}"
        python scripts/test_agent_standalone.py classifier "$QUERY"
        ;;

    technical)
        echo -e "${BLUE}Testing Technical Support Agent${NC}"
        python scripts/test_agent_standalone.py technical "$QUERY"
        ;;

    billing)
        echo -e "${BLUE}Testing Billing Support Agent${NC}"
        python scripts/test_agent_standalone.py billing "$QUERY"
        ;;

    general)
        echo -e "${BLUE}Testing General Support Agent${NC}"
        python scripts/test_agent_standalone.py general "$QUERY"
        ;;

    escalation)
        echo -e "${BLUE}Testing Escalation Evaluator Agent${NC}"
        python scripts/test_agent_standalone.py escalation "$QUERY"
        ;;

    response)
        echo -e "${BLUE}Testing Response Generator Agent${NC}"
        python scripts/test_agent_standalone.py response "$QUERY"
        ;;

    all)
        echo -e "${BLUE}Testing ALL Agents with sample queries${NC}"
        echo ""

        echo -e "${YELLOW}1. Intake Agent${NC}"
        python scripts/test_agent_standalone.py intake "My application is crashing" 2>&1 | head -30
        sleep 1

        echo -e "\n${YELLOW}2. FAQ Lookup Agent${NC}"
        python scripts/test_agent_standalone.py faq "How do I reset my password?" 2>&1 | head -30
        sleep 1

        echo -e "\n${YELLOW}3. Classifier Agent${NC}"
        python scripts/test_agent_standalone.py classifier "I was charged twice" 2>&1 | head -30
        sleep 1

        echo -e "\n${YELLOW}4. Technical Agent${NC}"
        python scripts/test_agent_standalone.py technical "App crashes when uploading files" 2>&1 | head -30
        sleep 1

        echo -e "\n${YELLOW}5. Billing Agent${NC}"
        python scripts/test_agent_standalone.py billing "Cancel my subscription" 2>&1 | head -30
        sleep 1

        echo -e "\n${YELLOW}6. General Agent${NC}"
        python scripts/test_agent_standalone.py general "How do I change my email?" 2>&1 | head -30
        sleep 1

        echo -e "\n${YELLOW}7. Escalation Agent${NC}"
        python scripts/test_agent_standalone.py escalation "This is unacceptable!" 2>&1 | head -30
        sleep 1

        echo -e "\n${YELLOW}8. Response Agent${NC}"
        python scripts/test_agent_standalone.py response "Password reset help" 2>&1 | head -30

        echo -e "\n${GREEN}All agents tested!${NC}"
        ;;

    list|--list|-l)
        python scripts/test_agent_standalone.py --list
        ;;

    help|--help|-h|"")
        echo "Usage: ./scripts/run_individual_agents.sh <agent> \"<query>\""
        echo ""
        echo "Agents:"
        echo "  intake      - Test Intake Agent"
        echo "  faq         - Test FAQ Lookup Agent"
        echo "  classifier  - Test Classifier Agent"
        echo "  technical   - Test Technical Support Agent"
        echo "  billing     - Test Billing Support Agent"
        echo "  general     - Test General Support Agent"
        echo "  escalation  - Test Escalation Agent"
        echo "  response    - Test Response Generator Agent"
        echo "  all         - Test all agents with sample queries"
        echo "  list        - List all available agents"
        echo ""
        echo "Examples:"
        echo "  ./scripts/run_individual_agents.sh intake \"My app crashes\""
        echo "  ./scripts/run_individual_agents.sh classifier \"Billing question\""
        echo "  ./scripts/run_individual_agents.sh all"
        ;;

    *)
        echo -e "${RED}Unknown agent: $AGENT${NC}"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
