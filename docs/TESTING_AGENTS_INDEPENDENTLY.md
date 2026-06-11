# Testing Agents Independently

Comprehensive guide to testing each agent in isolation.

## Overview

The multi-agent system allows you to test each agent independently without running the entire workflow. This is useful for:

- **Development**: Test agent changes in isolation
- **Debugging**: Identify issues in specific agents
- **Experimentation**: Try different prompts and inputs
- **Learning**: Understand how each agent works
- **Integration**: Test agents before integrating into workflow

## Three Ways to Test Agents

### 1. Unit Tests (Mocked - Fast)

**Location**: `tests/test_*_agent.py`

Unit tests use mocked LLM responses and run without API calls.

```bash
# Test single agent
pytest tests/test_intake_agent.py -v
pytest tests/test_classifier_agent.py -v

# Test specific test
pytest tests/test_intake_agent.py::TestIntakeAgent::test_intake_agent_urgent_priority -v

# Test all agents
pytest tests/ -v
```

**Pros**:
- ✅ Fast (<2 seconds for all 77 tests)
- ✅ No API costs
- ✅ No API key required
- ✅ Deterministic results
- ✅ Great for CI/CD

**Cons**:
- ❌ Doesn't test real LLM behavior
- ❌ Mocked responses may not match real outputs

### 2. Integration Tests (Real API - Accurate)

**Location**: `tests/integration/test_agents_independently.py`

Integration tests use real OpenAI API calls.

```bash
# Requires OPENAI_API_KEY environment variable
export OPENAI_API_KEY=sk-your-key-here

# Test single agent
pytest tests/integration/test_agents_independently.py::TestIntakeAgentIndependent -v -s

# Test all agents (will make real API calls)
pytest tests/integration/test_agents_independently.py -v -s

# Test specific agent
pytest tests/integration/ -k "ClassifierAgentIndependent" -v -s
```

**Pros**:
- ✅ Tests real LLM behavior
- ✅ Accurate results
- ✅ Catches real-world issues
- ✅ Validates prompt engineering

**Cons**:
- ❌ Requires API key
- ❌ Costs money (API usage)
- ❌ Slower (~2-3 seconds per test)
- ❌ Non-deterministic results

### 3. Standalone Scripts (Interactive - Visual)

**Location**: `scripts/test_agent_standalone.py`

Interactive script for testing individual agents with custom queries.

```bash
# Test with custom query
python scripts/test_agent_standalone.py intake "My app is crashing"
python scripts/test_agent_standalone.py classifier "I was charged twice"
python scripts/test_agent_standalone.py technical "App crashes on file upload"

# List all available agents
python scripts/test_agent_standalone.py --list

# Convenience wrapper script
./scripts/run_individual_agents.sh intake "My app crashes"
./scripts/run_individual_agents.sh all  # Test all agents
```

**Pros**:
- ✅ Interactive and visual
- ✅ Custom queries
- ✅ Easy to use
- ✅ Great for demonstrations
- ✅ Colored output

**Cons**:
- ❌ Requires API key
- ❌ Costs money (API usage)
- ❌ Manual testing

---

## Agent-by-Agent Testing Guide

### 1. Intake Agent

**Purpose**: Extract key information and set priority

**Test with Unit Tests**:
```bash
pytest tests/test_intake_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestIntakeAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py intake "URGENT: My application is crashing!"
```

**Expected Output**:
- Sets `priority` (low/medium/high)
- Updates `timestamp`
- Adds entry to `conversation_history`

**Sample Queries**:
- "My app is crashing" → Should detect urgency
- "I was just wondering about a feature" → Should set low priority
- "CRITICAL system failure!" → Should set high priority

---

### 2. FAQ Lookup Agent

**Purpose**: Search knowledge base for matching answers

**Test with Unit Tests**:
```bash
pytest tests/test_faq_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestFAQAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py faq "How do I reset my password?"
```

**Expected Output**:
- Sets `faq_match` (answer string or empty)
- Adds entry to `conversation_history`

**Sample Queries**:
- "How do I reset my password?" → Should find FAQ match
- "Why is the sky blue?" → Should return NO_MATCH
- "How do I cancel my subscription?" → Should find FAQ match

---

### 3. Classifier Agent

**Purpose**: Categorize ticket into TECHNICAL/BILLING/GENERAL

**Test with Unit Tests**:
```bash
pytest tests/test_classifier_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestClassifierAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py classifier "My app crashes when I upload files"
```

**Expected Output**:
- Sets `category` (TECHNICAL/BILLING/GENERAL)
- Adds entry to `conversation_history`

**Sample Queries**:
- "My app crashes" → Should categorize as TECHNICAL
- "I was charged twice" → Should categorize as BILLING
- "How do I change my email?" → Should categorize as GENERAL

---

### 4. Technical Support Agent

**Purpose**: Provide technical troubleshooting and solutions

**Test with Unit Tests**:
```bash
pytest tests/test_technical_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestTechnicalAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py technical "Application crashes when uploading large files"
```

**Expected Output**:
- Sets `resolution` (detailed troubleshooting steps)
- Adds entry to `conversation_history`

**Sample Queries**:
- "App crashes on file upload" → Should provide troubleshooting steps
- "Error code 0x8007000E" → Should explain error and solutions
- "Slow performance" → Should suggest optimization steps

---

### 5. Billing Support Agent

**Purpose**: Handle billing and payment questions

**Test with Unit Tests**:
```bash
pytest tests/test_billing_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestBillingAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py billing "I was charged twice this month"
```

**Expected Output**:
- Sets `resolution` (billing explanation and next steps)
- Adds entry to `conversation_history`

**Sample Queries**:
- "I was charged twice" → Should explain refund process
- "How do I cancel my subscription?" → Should provide cancellation steps
- "Need a refund" → Should explain refund policy

---

### 6. General Support Agent

**Purpose**: Handle general inquiries and how-to questions

**Test with Unit Tests**:
```bash
pytest tests/test_general_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestGeneralAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py general "How do I change my email address?"
```

**Expected Output**:
- Sets `resolution` (step-by-step instructions)
- Adds entry to `conversation_history`

**Sample Queries**:
- "How do I reset my password?" → Should provide reset instructions
- "Change my email" → Should provide account management steps
- "What features are included?" → Should list features

---

### 7. Escalation Evaluator Agent

**Purpose**: Determine if human intervention is needed

**Test with Unit Tests**:
```bash
pytest tests/test_escalation_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestEscalationAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py escalation "I want to speak to a lawyer!"
```

**Expected Output**:
- Sets `needs_escalation` (true/false)
- Adds entry to `conversation_history`

**Sample Queries**:
- "This is unacceptable!" → Should escalate (keyword: "unacceptable")
- "I need a lawyer" → Should escalate (keyword: "lawyer")
- "How do I reset password?" → Should NOT escalate (simple query)

**Escalation Keywords**:
- lawsuit, lawyer, attorney, sue, legal action
- urgent, critical, emergency
- angry, frustrated, unacceptable

---

### 8. Response Generator Agent

**Purpose**: Create final customer-facing response

**Test with Unit Tests**:
```bash
pytest tests/test_response_agent.py -v
```

**Test with Integration Test**:
```bash
pytest tests/integration/test_agents_independently.py::TestResponseAgentIndependent -v -s
```

**Test with Standalone Script**:
```bash
python scripts/test_agent_standalone.py response "How do I reset my password?"
```

**Expected Output**:
- Sets `final_response` (professional email)
- Adds entry to `conversation_history`

**Expected Response Format**:
- Greeting
- Issue acknowledgment
- Solution/steps
- Ticket ID reference
- Closing with offer for further assistance

---

## Quick Reference Commands

### Test All Agents (Unit Tests - Fast)
```bash
pytest tests/ -v
```

### Test All Agents (Integration - Real API)
```bash
export OPENAI_API_KEY=sk-your-key-here
pytest tests/integration/ -v -s
```

### Test All Agents (Standalone - Interactive)
```bash
./scripts/run_individual_agents.sh all
```

### Test Single Agent (All Three Methods)
```bash
# Unit test (mocked)
pytest tests/test_intake_agent.py -v

# Integration test (real API)
pytest tests/integration/test_agents_independently.py::TestIntakeAgentIndependent -v -s

# Standalone (interactive)
python scripts/test_agent_standalone.py intake "My custom query"
```

---

## Testing Workflow

### Development Workflow

1. **Write Code**: Make changes to an agent
2. **Unit Test**: Run fast mocked tests
   ```bash
   pytest tests/test_intake_agent.py -v
   ```
3. **Integration Test**: Verify with real API
   ```bash
   pytest tests/integration/test_agents_independently.py::TestIntakeAgentIndependent -v -s
   ```
4. **Manual Test**: Try custom queries
   ```bash
   python scripts/test_agent_standalone.py intake "Test query"
   ```

### Debugging Workflow

1. **Identify Issue**: Notice agent behaving incorrectly
2. **Isolate**: Test just that agent
   ```bash
   python scripts/test_agent_standalone.py classifier "Problem query"
   ```
3. **Inspect**: Check output and state changes
4. **Fix**: Modify agent code
5. **Verify**: Re-run test to confirm fix

---

## Environment Setup

### Required Environment Variables

```bash
# For integration tests and standalone scripts
export OPENAI_API_KEY=sk-your-api-key-here

# Optional: Override default model
export OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# Optional: Override temperature
export TEMPERATURE=0.7
```

### Test Data Setup

The FAQ database must be present for FAQ agent tests:
```bash
# Verify FAQ database exists
ls data/faq_database.json

# If missing, copy example
cp data/faq_database.json.example data/faq_database.json
```

---

## Troubleshooting

### Issue: "No module named 'src'"

**Solution**: Run from project root
```bash
cd /path/to/payment-exception-resolution-model
python scripts/test_agent_standalone.py intake "test"
```

### Issue: "OPENAI_API_KEY not set"

**Solution**: Export API key
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Access denied" or "Permission denied error"

**Solution**: Check API key validity
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: Tests are slow

**Solution**: Use unit tests instead of integration tests
```bash
# Fast (mocked)
pytest tests/ -v

# Slow (real API)
pytest tests/integration/ -v
```

---

## Best Practices

### 1. Use Unit Tests for CI/CD
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest tests/ -v
```

### 2. Use Integration Tests for Validation
```bash
# Before deploying
pytest tests/integration/ -v -s
```

### 3. Use Standalone Scripts for Demos
```bash
# Show how classifier works
python scripts/test_agent_standalone.py classifier "I was charged twice"
```

### 4. Test Edge Cases
```bash
# Empty query
python scripts/test_agent_standalone.py intake ""

# Very long query
python scripts/test_agent_standalone.py intake "$(cat long_query.txt)"

# Special characters
python scripts/test_agent_standalone.py classifier "I need a refund!!! $$$$"
```

---

## Summary

| Method | Speed | Cost | API Key | Use Case |
|--------|-------|------|---------|----------|
| **Unit Tests** | ⚡ Fast | Free | ❌ No | Development, CI/CD |
| **Integration Tests** | 🐌 Slow | 💰 Paid | ✅ Yes | Validation, QA |
| **Standalone Scripts** | 🐌 Slow | 💰 Paid | ✅ Yes | Demos, Debugging |

**Recommendation**:
- Development: Use unit tests
- Pre-deployment: Run integration tests
- Demonstrations: Use standalone scripts
- CI/CD: Use unit tests only

---

## Additional Resources

- **Unit Test Documentation**: `tests/README.md`
- **Agent Code Walkthrough**: `docs/AGENT_CODE_WALKTHROUGH.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Architecture Overview**: `docs/ARCHITECTURE.md`
