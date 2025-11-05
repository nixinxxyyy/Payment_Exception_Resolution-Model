# Customer Support Ticket Workflow - Flow Diagram

> **Note:** Image versions (PNG/SVG) of all diagrams are available in the [`diagrams/`](./diagrams/) directory. These are ready to use in presentations, documentation, or anywhere you need visual representations.

## Complete Multi-Agent System Flow

![Complete Workflow](./diagrams/complete-workflow.png)

```mermaid
flowchart TD
    Start([Customer Query]) --> Intake[Intake Agent]

    Intake --> |Extract Info| FAQ[FAQ Lookup Agent]

    FAQ --> |Search FAQ DB| FAQDecision{FAQ Match?}

    FAQDecision --> |YES - Match Found| FAQYes[Set faq_match = Answer]
    FAQDecision --> |NO - No Match| FAQNo[Set faq_match = empty]

    FAQYes --> Classifier[Classifier Agent]
    FAQNo --> Classifier

    Classifier --> |Categorize| RouteDecision{Category?}

    RouteDecision --> |TECHNICAL| Technical[Technical Support Agent]
    RouteDecision --> |BILLING| Billing[Billing Support Agent]
    RouteDecision --> |GENERAL| General[General Support Agent]

    Technical --> |With FAQ Context| TechProcess[Generate Resolution<br/>Uses: FAQ Match + Query]
    Billing --> |With FAQ Context| BillProcess[Generate Resolution<br/>Uses: FAQ Match + Query]
    General --> |With FAQ Context| GenProcess[Generate Resolution<br/>Uses: FAQ Match + Query]

    TechProcess --> Escalation[Escalation Evaluator]
    BillProcess --> Escalation
    GenProcess --> Escalation

    Escalation --> |Evaluate| EscDecision{Needs<br/>Escalation?}

    EscDecision --> |YES| EndEscalated([END - Human Agent])
    EscDecision --> |NO| Response[Response Generator]

    Response --> |Create Final Response| EndSuccess([END - Automated Response])

    style FAQYes fill:#90EE90
    style FAQNo fill:#FFB6C1
    style Technical fill:#87CEEB
    style Billing fill:#87CEEB
    style General fill:#87CEEB
    style EndEscalated fill:#FF6B6B
    style EndSuccess fill:#51CF66
```

## FAQ Match vs No Match - Detailed Comparison

```mermaid
flowchart LR
    subgraph "FAQ Match Found"
        Q1[Customer Query:<br/>'How do I reset password?'] --> F1[FAQ Agent]
        F1 --> M1[Match Found:<br/>'Go to Settings > Reset']
        M1 --> S1[Specialized Agent]
        S1 --> R1[Resolution:<br/>FAQ answer +<br/>personalization +<br/>empathy]
    end

    subgraph "No FAQ Match"
        Q2[Customer Query:<br/>'App crashes on iOS 18'] --> F2[FAQ Agent]
        F2 --> M2[No Match:<br/>faq_match = empty]
        M2 --> S2[Specialized Agent]
        S2 --> R2[Resolution:<br/>LLM generates<br/>from scratch using<br/>domain knowledge]
    end

    style M1 fill:#90EE90
    style M2 fill:#FFB6C1
    style R1 fill:#B4E7CE
    style R2 fill:#FFD4A3
```

## State Flow Through Agents

```mermaid
graph TD
    subgraph "Initial State"
        S1[customer_query: string<br/>ticket_id: generated<br/>faq_match: ?<br/>category: ?<br/>resolution: ?<br/>needs_escalation: ?]
    end

    subgraph "After FAQ Agent"
        S2A[FAQ MATCH:<br/>faq_match: FAQ answer<br/>history: Match found]
        S2B[NO MATCH:<br/>faq_match: empty<br/>history: No match found]
    end

    subgraph "After Classifier"
        S3[category: TECHNICAL/BILLING/GENERAL<br/>priority: low/medium/high]
    end

    subgraph "After Specialized Agent"
        S4A[WITH FAQ:<br/>resolution: Enhanced FAQ answer]
        S4B[NO FAQ:<br/>resolution: Original solution]
    end

    subgraph "After Escalation Check"
        S5A[needs_escalation: true<br/>→ Human agent]
        S5B[needs_escalation: false<br/>→ Response generator]
    end

    subgraph "Final State"
        S6[final_response: Polished email<br/>status: complete]
    end

    S1 --> S2A
    S1 --> S2B
    S2A --> S3
    S2B --> S3
    S3 --> S4A
    S3 --> S4B
    S4A --> S5A
    S4A --> S5B
    S4B --> S5A
    S4B --> S5B
    S5B --> S6

    style S2A fill:#90EE90
    style S2B fill:#FFB6C1
    style S4A fill:#B4E7CE
    style S4B fill:#FFD4A3
    style S5A fill:#FF6B6B
    style S6 fill:#51CF66
```

## Agent Processing Details

```mermaid
sequenceDiagram
    participant C as Customer
    participant I as Intake Agent
    participant F as FAQ Agent
    participant CL as Classifier
    participant S as Specialized Agent
    participant E as Escalation Check
    participant R as Response Gen

    C->>I: Submit Query
    I->>I: Extract key info<br/>Set priority
    I->>F: Pass state

    alt FAQ Match Found
        F->>F: Search FAQ DB<br/>LLM semantic match
        F->>F: Set faq_match = answer
        Note over F: state["faq_match"] = "Go to Settings..."
    else No FAQ Match
        F->>F: Search FAQ DB<br/>LLM returns NO_MATCH
        F->>F: Set faq_match = empty
        Note over F: state["faq_match"] = ""
    end

    F->>CL: Pass state
    CL->>CL: Categorize ticket
    CL->>S: Route by category

    alt With FAQ Context
        S->>S: Generate resolution<br/>FAQ: Go to Settings...<br/>→ Build upon FAQ
    else Without FAQ Context
        S->>S: Generate resolution<br/>FAQ: None<br/>→ Create from scratch
    end

    S->>E: Pass state with resolution

    alt Needs Escalation
        E->>C: Route to human agent
    else No Escalation Needed
        E->>R: Generate final response
        R->>C: Send polished response
    end
```

## Key Decision Points

| Decision Point | Location | Conditions | Outcomes |
|---------------|----------|-----------|----------|
| **FAQ Match** | FAQ Agent | LLM semantic match != "NO_MATCH" | ✅ Set faq_match<br/>❌ Set empty |
| **Category Route** | Classifier | Category classification | → Technical<br/>→ Billing<br/>→ General |
| **Escalation** | Escalation Check | Keywords + complexity + sentiment | ✅ Human agent<br/>❌ Auto response |

## State Changes Through Workflow

```
START
├── ticket_id: "TKT-001"
├── customer_query: "How do I reset my password?"
├── faq_match: ""
└── conversation_history: []

AFTER INTAKE
├── priority: "medium"
├── timestamp: "2025-10-25T10:30:00"
└── conversation_history: ["[INTAKE] Password reset query identified"]

AFTER FAQ (Match Found)
├── faq_match: "Go to Settings > Security > Reset Password"
└── conversation_history: ["[INTAKE]...", "[FAQ] Match found: Go to Settings..."]

AFTER FAQ (No Match)
├── faq_match: ""
└── conversation_history: ["[INTAKE]...", "[FAQ] No direct match found"]

AFTER CLASSIFIER
├── category: "TECHNICAL"
└── conversation_history: ["...", "[CLASSIFIER] Categorized as TECHNICAL"]

AFTER SPECIALIZED AGENT (With FAQ)
├── resolution: "Based on your query, here's how to reset...<FAQ content + details>"
└── conversation_history: ["...", "[TECHNICAL] Resolution provided"]

AFTER SPECIALIZED AGENT (No FAQ)
├── resolution: "Let me help you troubleshoot this issue... <generated solution>"
└── conversation_history: ["...", "[TECHNICAL] Resolution provided"]

AFTER ESCALATION CHECK
├── needs_escalation: false
└── conversation_history: ["...", "[ESCALATION] No escalation needed"]

AFTER RESPONSE GENERATOR
├── final_response: "Dear Customer,\n\nThank you for reaching out...\n\nTicket: TKT-001"
└── conversation_history: ["...", "[RESPONSE] Final response generated"]

END
```

## Viewing the Diagram

To view this diagram:
1. **GitHub/GitLab**: Automatically renders Mermaid diagrams
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **Online**: Copy to https://mermaid.live
4. **Documentation sites**: Most modern docs platforms support Mermaid

## Architecture Highlights

✅ **No Short-Circuits**: FAQ match doesn't skip agents
✅ **Context-Aware**: FAQ informs but doesn't dictate
✅ **Consistent Flow**: Same path regardless of FAQ match
✅ **Safety Net**: Escalation evaluates all tickets
✅ **State Persistence**: All agent decisions tracked in conversation_history
