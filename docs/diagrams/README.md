# Workflow Diagrams

This directory contains visual representations of the customer support ticket management system workflow.

## Available Diagrams

### 1. Complete Workflow
**Files:** `complete-workflow.png` | `complete-workflow.svg` | `complete-workflow.mmd`

Shows the entire multi-agent system flow from customer query to final response, including:
- All agent nodes (Intake, FAQ, Classifier, Specialized Agents, Escalation, Response)
- Decision points (FAQ match, category routing, escalation check)
- Two possible end states (Human agent vs Automated response)

**Use this diagram for:** Understanding the overall system architecture and flow

---

### 2. FAQ Comparison
**Files:** `faq-comparison.png` | `faq-comparison.svg` | `faq-comparison.mmd`

Side-by-side comparison showing:
- **Left:** What happens when FAQ match is found
- **Right:** What happens when no FAQ match exists

Highlights how FAQ matches inform (but don't dictate) the specialized agent's response.

**Use this diagram for:** Explaining the difference between FAQ-informed and original resolutions

---

### 3. State Flow
**Files:** `state-flow.png` | `state-flow.svg` | `state-flow.mmd`

Shows how the `TicketState` object transforms as it flows through agents:
- Initial state structure
- Changes after each agent
- Branching paths for FAQ match/no match
- Escalation decision paths
- Final state structure

**Use this diagram for:** Understanding state management and data flow

---

### 4. Sequence Diagram
**Files:** `sequence-diagram.png` | `sequence-diagram.svg` | `sequence-diagram.mmd`

Detailed sequence showing interactions between:
- Customer
- All agents (Intake → FAQ → Classifier → Specialized → Escalation → Response)
- Decision branches (alt blocks for FAQ match and escalation)

**Use this diagram for:** Understanding the temporal flow and agent communication

---

## File Formats

### PNG (.png)
- **Best for:** Documentation, presentations, embedding in markdown
- **Advantages:** Universal support, good quality
- **File size:** Larger (63KB - 129KB)

### SVG (.svg)
- **Best for:** Web pages, scalable presentations, print
- **Advantages:** Infinite scalability, smaller file size
- **File size:** Smaller (19KB - 162KB)

### Mermaid (.mmd)
- **Best for:** Editing, source control, regenerating diagrams
- **Advantages:** Text-based, version control friendly
- **File size:** Very small (0.7KB - 1.5KB)

---

## Usage Examples

### In Markdown
```markdown
![Complete Workflow](./diagrams/complete-workflow.png)
```

### In HTML
```html
<img src="./diagrams/complete-workflow.svg" alt="Complete Workflow" />
```

### In Presentations
Use the PNG files for PowerPoint/Keynote, or SVG for web-based presentations.

---

## Regenerating Diagrams

If you need to regenerate the diagrams after editing the `.mmd` files:

```bash
# Install Mermaid CLI (if not already installed)
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i complete-workflow.mmd -o complete-workflow.png -b transparent

# Generate SVG
mmdc -i complete-workflow.mmd -o complete-workflow.svg
```

---

## Color Legend

| Color | Meaning |
|-------|---------|
| 🟢 Green (#90EE90, #B4E7CE, #51CF66) | FAQ match found, success paths, completed states |
| 🔴 Pink/Red (#FFB6C1, #FF6B6B) | No FAQ match, escalation to human |
| 🔵 Blue (#87CEEB) | Specialized agents (Technical, Billing, General) |
| 🟡 Orange (#FFD4A3) | Generated solutions without FAQ context |

---

## Diagram Descriptions

### Complete Workflow Details
- **Entry Point:** Customer Query
- **Linear Flow:** Intake → FAQ → Classifier
- **Conditional Routing:** Category-based (3 specialized agents)
- **Escalation Logic:** Evaluates keywords, sentiment, complexity
- **Exit Points:** Human agent OR Automated response

### FAQ Agent Logic
- Loads FAQ database from `data/faq_database.json`
- Uses LLM semantic matching (temperature=0.3 for deterministic results)
- Returns exact FAQ answer or "NO_MATCH"
- FAQ context passed to all downstream agents

### Specialized Agent Behavior
- **With FAQ match:** Enhances FAQ answer with empathy, formatting, specifics
- **Without FAQ match:** Generates original solution using domain knowledge
- All agents receive: query, priority, FAQ match (if any)

### Escalation Criteria
- Keywords: lawsuit, lawyer, urgent, critical, angry
- Low confidence in resolution
- Complex technical issues requiring human expertise
- Customer sentiment analysis

---

## Questions?

For more details on the workflow architecture, see:
- Main documentation: `../workflow-diagram.md`
- Source code: `../../src/workflow.py`
- Agent implementations: `../../src/agents/`
