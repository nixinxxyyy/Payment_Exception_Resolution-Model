# Test Suite for Multi-Agent Ticket Management System

Comprehensive test suite for all 8 agents in the customer support ticket management system.

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures and mocks
├── test_intake_agent.py         # Tests for Intake Agent
├── test_faq_agent.py            # Tests for FAQ Lookup Agent
├── test_classifier_agent.py     # Tests for Classifier Agent
├── test_technical_agent.py      # Tests for Technical Support Agent
├── test_billing_agent.py        # Tests for Billing Support Agent
├── test_general_agent.py        # Tests for General Support Agent
├── test_escalation_agent.py     # Tests for Escalation Evaluator Agent
└── test_response_agent.py       # Tests for Response Generator Agent
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_intake_agent.py -v

# Run specific test
pytest tests/test_intake_agent.py::TestIntakeAgent::test_intake_agent_urgent_priority -v
```

### Run Tests by Agent

```bash
# Intake Agent
pytest tests/test_intake_agent.py -v

# FAQ Lookup Agent
pytest tests/test_faq_agent.py -v

# Classifier Agent
pytest tests/test_classifier_agent.py -v

# Technical Support Agent
pytest tests/test_technical_agent.py -v

# Billing Support Agent
pytest tests/test_billing_agent.py -v

# General Support Agent
pytest tests/test_general_agent.py -v

# Escalation Agent
pytest tests/test_escalation_agent.py -v

# Response Generator Agent
pytest tests/test_response_agent.py -v
```

### Run Tests with Markers

```bash
# Run only fast tests (no API calls)
pytest tests/ -v -m "not slow"

# Run with verbose output
pytest tests/ -vv

# Run with test output
pytest tests/ -v -s
```

## Test Coverage

Each agent test file includes:

- ✅ **Basic functionality tests** - Core agent operations
- ✅ **State preservation tests** - Ensures agents don't modify unrelated state
- ✅ **Conversation history tests** - Verifies history is properly appended
- ✅ **Edge case tests** - Handles empty, null, or invalid inputs
- ✅ **Integration tests** - Tests with realistic ticket states

### Test Statistics

| Agent | Test Count | Coverage |
|-------|-----------|----------|
| Intake Agent | 8 tests | Priority detection, urgency keywords |
| FAQ Lookup Agent | 10 tests | Match finding, empty database, file loading |
| Classifier Agent | 11 tests | All categories, invalid inputs, normalization |
| Technical Agent | 8 tests | Resolution generation, complex issues |
| Billing Agent | 8 tests | Refunds, subscriptions, payments |
| General Agent | 8 tests | How-to questions, account management |
| Escalation Agent | 15 tests | Keyword detection, LLM decisions |
| Response Generator | 11 tests | Professional tone, all categories |
| **Total** | **79 tests** | **Comprehensive coverage** |

## Fixtures

The `conftest.py` file provides reusable fixtures:

### State Fixtures

- `base_ticket_state` - Generic ticket state
- `technical_ticket_state` - Technical issue state
- `billing_ticket_state` - Billing issue state
- `general_ticket_state` - General inquiry state
- `urgent_ticket_state` - High-priority state
- `escalation_ticket_state` - State requiring escalation
- `classified_ticket_state` - Already classified state
- `resolved_ticket_state` - State with resolution

### Data Fixtures

- `sample_faq_database` - Mock FAQ database with 5 entries

### Mock Fixtures

- `mock_llm_response` - Creates mock LLM responses
- `mock_chatgpt` - Mocks ChatOpenAI to avoid API calls

## Test Independence

All tests are designed to run independently:

- ✅ **No shared state** between tests
- ✅ **No API calls** - All LLM interactions are mocked
- ✅ **No database dependencies** - Uses in-memory fixtures
- ✅ **No file system dependencies** - Mocks file operations
- ✅ **Fast execution** - All tests complete in seconds

## Mocking Strategy

The test suite uses comprehensive mocking to avoid external dependencies:

### 1. LLM Mocking

```python
# All OpenAI API calls are mocked
mock_chatgpt("TECHNICAL")  # Returns this as LLM response
```

### 2. File System Mocking

```python
# FAQ database loading is mocked
monkeypatch.setattr("src.agents.faq_agent.load_faq_database", lambda: sample_faq_database)
```

### 3. Configuration Mocking

```python
# Configuration values are accessed from the config singleton
# No need to mock if using default values
```

## Test Examples

### Example: Testing Priority Detection

```python
def test_intake_agent_urgent_priority(self, base_ticket_state, mock_chatgpt):
    """Test that urgent keywords are detected and priority is set to high."""
    base_ticket_state["customer_query"] = "URGENT: I need immediate help!"
    mock_chatgpt("Customer needs urgent assistance.")

    result = intake_agent(base_ticket_state)

    assert result["priority"] == "high"
```

### Example: Testing Category Classification

```python
def test_classifier_technical_category(self, technical_ticket_state, mock_chatgpt):
    """Test classification of technical issues."""
    mock_chatgpt("TECHNICAL")

    result = classifier_agent(technical_ticket_state)

    assert result["category"] == "TECHNICAL"
```

### Example: Testing Escalation

```python
def test_escalation_agent_keyword_auto_escalate(self, escalation_ticket_state):
    """Test that escalation keywords trigger automatic escalation."""
    # Query contains "lawyer" - should auto-escalate
    result = escalation_evaluator_agent(escalation_ticket_state)

    assert result["needs_escalation"] is True
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov=src
```

## Test Data

All test data is self-contained in fixtures:

- Realistic customer queries
- Multiple ticket states
- Sample FAQ database
- Various priority levels
- All category types

## Debugging Tests

### Run with debugging

```bash
# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb

# Show print statements
pytest tests/ -s

# Show local variables on failure
pytest tests/ -l
```

### View test output

```bash
# Detailed output
pytest tests/ -vv

# Show test durations
pytest tests/ --durations=10
```

## Adding New Tests

To add tests for a new agent:

1. Create `test_<agent_name>.py` in the `tests/` directory
2. Import the agent function
3. Create test class inheriting from object
4. Use fixtures from `conftest.py`
5. Mock LLM responses with `mock_chatgpt`
6. Assert expected state changes

Example template:

```python
"""Tests for New Agent."""

import pytest
from src.agents.new_agent import new_agent


class TestNewAgent:
    """Test suite for New Agent."""

    def test_basic_functionality(self, base_ticket_state, mock_chatgpt):
        """Test basic agent operation."""
        mock_chatgpt("Expected response")

        result = new_agent(base_ticket_state)

        assert result["expected_field"] == "expected_value"
```

## Best Practices

1. ✅ **One test, one assertion focus** - Test one thing per test
2. ✅ **Clear test names** - Use descriptive names that explain what's being tested
3. ✅ **Use fixtures** - Reuse common state setups
4. ✅ **Mock external dependencies** - No real API calls
5. ✅ **Test edge cases** - Empty inputs, invalid data, etc.
6. ✅ **Verify state preservation** - Ensure unrelated fields aren't modified
7. ✅ **Test conversation history** - Verify proper logging

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're running from project root
cd /path/to/customer-support-ticket-mgmt-multi-agent-system
pytest tests/
```

**Mock not working:**
```python
# Ensure mock path matches import path in agent file
monkeypatch.setattr("src.agents.intake_agent.ChatOpenAI", mock_llm_class)
```

**Fixture not found:**
```python
# Ensure conftest.py is in the tests/ directory
# Pytest automatically discovers conftest.py
```

## Dependencies

Required packages for testing:

```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

Install with:

```bash
pip install pytest pytest-cov pytest-mock
```

## Test Maintenance

- **Update fixtures** when state structure changes
- **Update mocks** when agent signatures change
- **Add tests** for new features
- **Remove tests** for deprecated features
- **Keep tests fast** - No slow operations

## Performance

All 79 tests run in **under 5 seconds** due to:

- No real API calls (mocked)
- No file system operations (mocked)
- No database queries (in-memory fixtures)
- Independent tests (no setup/teardown overhead)

## Next Steps

- [ ] Add integration tests for full workflow
- [ ] Add performance/benchmark tests
- [ ] Add stress tests with concurrent tickets
- [ ] Add tests for API endpoints
- [ ] Add tests for configuration validation
