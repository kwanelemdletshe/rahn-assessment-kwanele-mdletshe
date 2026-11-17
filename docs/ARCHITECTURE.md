# Software Architecture Document
## Project: FitDesk Enquiry Assistant

### 1. System Overview
The FitDesk Enquiry Assistant is built as a lightweight, single-process command-line interface (CLI) application in Python. It complies with the **RAHN Mandatory Framework for Intern Execution**, separating data ingestion, LLM reasoning, deterministic business rule constraints, and state tracking via clear module boundaries.

┌───────────────────────┐
│   Command Line (CLI)  │
└───────────┬───────────┘
│ Inbound Query String
▼
┌───────────────────────┐
│     LLM Reasoning     │ ◄─── Pydantic Validation
│ (Gemini API / Struct) │      (Schema Enforcement)
└───────────┬───────────┘
│ Validated JSON JSON Object
▼
┌───────────────────────┐
│   Tool & Data Gate   │ ◄─── Local Database
│  (Grounded Lookups)   │      (data.json / CSV)
└───────────┬───────────┘
│ Grounded Response Draft
▼
┌───────────────────────┐
│  Human Approval Gate  │ ◄─── Terminal y/n Intercept
└───────────┬───────────┘
│ Approved Payload
▼
┌───────────────────────┐
│      Output Logs      │ ───► status_log.json
└───────────────────────┘

### 2. Project Directory Structure
To maintain an auditable submission, the repository must be organized exactly as follows:
```text
rahn-assessment-firstname-lastname/  # All lowercase as required by Rule 7
│
├── docs/
│   ├── SRS.md                      # Mini-SRS Specification
│   ├── PROJECT_PLAN.md             # Timeline & Milestones
│   ├── ARCHITECTURE.md             # System Architecture Design
│   ├── REGRESSION_TESTS.md         # Manual & Automated Test Matrix
│   └── RAPLH_LOG.md                # Controlled Agent Optimization Log
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # Main CLI Application entry point
│   ├── schema.py                   # Pydantic structured output models
│   └── database.py                 # Local JSON lookup operations handler
│
├── tests/
│   ├── __init__.py
│   └── test_assistant.py           # Automated unit tests using pytest & mock
│
├── data/
│   └── data.json                   # Authorized package and availability data
│
├── status_log.json                 # Operational log file (generated at runtime)
├── .env                            # Secret keys (listed in .gitignore)
├── .env.example                    # Template environment variables file
├── .gitignore                      # Enforces exclusion of .env and local caches
├── README.md                       # Installation and setup execution steps
└── requirements.txt                # Third-party dependency definitions
```

### 3. Core Component Mappings
*   **Ingestion & Orchestration (`src/main.py`):** Captures the raw terminal text argument string. It calls the Gemini API model endpoints, routes output through Pydantic structures, triggers the lookup sequence, and halts processing for user authorization strings.
*   **Schema Validation (`src/schema.py`):** Declares strict type definitions for interpretation outputs using Pydantic fields. This completely decouples reasoning extraction from business text formatting.
*   **Fact Repository Gate (`src/database.py`):** Acts as the system's "Tool Constraint" layer. It loads static data from `data/data.json` and uses explicit dictionary matching. If matching keys are missing, it throws an exact escalation response.

### 4. Technical Specifications & Pydantic Definitions
The system leverages Google Gemini’s structured output capabilities to map the user input into a predictable typed data record.

#### Pydantic Model (`src/schema.py`)
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class EnquiryAnalysis(BaseModel):
    intent: str = Field(
        description="The primary category of enquiry. Must be one of: 'package_enquiry', 'availability_enquiry', 'mixed_enquiry', or 'unknown'."
    )
    extracted_package_type: Optional[str] = Field(
        default=None, 
        description="Extracted package keyword requested by user (e.g., 'single_session', '5_sessions', '12_sessions')."
    )
    extracted_time_slot: Optional[str] = Field(
        default=None, 
        description="Extracted target time slot requested by user in HH:MM format (e.g., '09:00', '10:00', '11:00')."
    )
    requires_human_approval: bool = Field(
        default=True,
        description="Mandatory flag. Always returns True as per the RAHN Human-in-the-Loop policy."
    )
```

#### Local Authorized Fact Database Layout (`data/data.json`)
```json
{
  "packages": {
    "single_session": "R180",
    "5_sessions": "R800",
    "12_sessions": "R1,680"
  },
  "saturday_availability": {
    "09:00": "Available",
    "10:00": "Full",
    "11:00": "Available"
  }
}
```

### 5. Deterministic Data Flow Pipeline
1.  The app takes an inbound query from the CLI terminal interface.
2.  The input string passes to the Gemini API (`gemini-2.5-flash` or similar) configured with `response_mime_type="application/json"` and structural schema mappings tied to `EnquiryAnalysis`.
3.  The response parses into a validated object using Pydantic.
4.  `src/database.py` receives the model values and runs exact matching checks against `data/data.json`.
5.  **Grounding Rule Evaluation:**
    *   *If parameters match data:* Construct text response explicitly stating verified prices/slots.
    *   *If parameters do not match or keys are missing:* Inject the exact fallback string: `"I'll check with the owner and come back to you."`
6.  The user interface outputs the draft and intercepts flow using standard prompt controls (`Send? (y/n)`).
7.  If confirmed (`y`), write state to `status_log.json` as `"sent"`. If (`n`), discard string modifications and save as `"rejected"`.