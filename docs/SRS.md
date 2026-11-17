# Software Requirements Specification (SRS)
## Project: FitDesk Enquiry Assistant

### 1. Business Objective
The objective is to provide the owner of a small fitness studio in Hermanus with a command-line AI assistant that safely automates the understanding of customer enquiries and drafting of responses regarding session packages and Saturday availability. The tool intends to eliminate the immediate manual drafting burden for studio staff while enforcing an absolute zero-hallucination policy and requiring manual confirmation before any log entry is recorded as sent.

### 2. Stakeholders
*   **Studio Owner:** Wants administrative relief without risking business reputation through incorrect pricing or availability commitments.
*   **Studio Staff Members:** The primary operators who interact with the command-line tool, reviewing, modifying, and approving drafts.
*   **Prospective / Existing Customers:** Individuals making inbound enquiries who receive accurate, consistent information regarding studio services.

### 3. Scope Boundaries
#### In-Scope
*   Accepting customer text enquiries via command-line input.
*   Structured intent classification and parameter extraction via Google Gemini API validated against a Pydantic model.
*   Local data lookups against an authorized file containing session packaging, pricing, and specific Saturday time-slot availability status.
*   Deterministic text drafting using strictly grounded facts or an exact fallback escalation phrase.
*   An interactive manual human approval gate (y/n toggle) for operators.
*   Local file status logging of all interactions.

#### Out-of-Scope
*   Direct WhatsApp Business API integrations or live webhooks.
*   Automated calendar bookings or Google Calendar modifications.
*   Payment gateway processing (e.g., PayFast integration).
*   Dynamic scheduling adjustments, pricing negotiations, or multi-turn conversational persistence.

### 4. Functional Requirements (FR)
*   **FR-01 (Inbound Ingestion):** The system must accept a single customer query string submitted via a terminal command-line prompt.
*   **FR-02 (Structured Intent Extraction):** The system must pass the inbound query to the Gemini API and enforce a structured JSON response containing at least three attributes: `intent`, `details`, and `requires_human_approval`. This output must successfully instantiate a Pydantic schema.
*   **FR-03 (Fact Retrieval & Grounding):** The system must cross-reference extracted query fields against an authorized local file containing package definitions (Single session: R180, 5 sessions: R800, 12 sessions: R1680) and Saturday slots (09:00: Available, 10:00: Full, 11:00: Available).
*   **FR-04 (Draft Generation & Fallback):** The system must compile a drafted answer containing only verified facts from the data file. If any requested package or slot parameter does not exist in the local file, the system must generate the exact fallback text: *"I'll check with the owner and come back to you."*
*   **FR-05 (Human-in-the-Loop Gate):** The system must print the compiled response draft to the terminal console and halt execution to await an explicit staff confirmation string prompt (`Send? (y/n)`).
*   **FR-06 (Auditable Status Logging):** The system must append the operational result of the interaction to a local `status_log.json` file, tracking timestamps, customer queries, intent mapping, generated drafts, and final dispatch confirmation status.

### 5. Non-Functional Requirements (NFR)
*   **NFR-01 (Reliability & Safety Guard):** Under no circumstances shall a status of `"sent"` be appended to the state log if the operator selects `n`, the Gemini API times out, or the returned payload breaches Pydantic typing rules.
*   **NFR-02 (Security & Credentials):** The application must extract credentials strictly from a localized environment runtime (`.env`). No cleartext Google Gemini API keys may be hardcoded or checked into version control repositories.
*   **NFR-03 (Data Execution Footprint):** The local fact repository must be decoupled from code components, operating out of a standard flat file architecture (`.json` or `.csv`) for trivial updates by non-technical managers.

### 6. Data Inputs & Outputs
#### Data Inputs
*   **User CLI Prompt String:** Raw text provided by an operator mimicking an incoming message (e.g., *"How much is the 12-session pack and do you have Saturday slots?"*).
*   **Authorized Facts Storage (`data.json`):**
    ```json
    {
      "packages": {
        "single_session": 180,
        "5_sessions": 800,
        "12_sessions": 1680
      },
      "saturday_availability": {
        "09:00": "Available",
        "10:00": "Full",
        "11:00": "Available"
      }
    }
    ```
*   **Gemini API Structural Schema Constraints:** Standard Pydantic blueprint used to parse structured output models.

#### Data Outputs
*   **Terminal Interface Printouts:** Formatted draft blocks followed by an interactive console evaluation string (`Send? (y/n)`).
*   **Transaction State Appendices (`status_log.json`):**
    ```json
    {
      "timestamp": "2026-11-15T11:44:00Z",
      "customer_query": "How much is the 12-session pack?",
      "extracted_intent": "package_enquiry",
      "generated_draft": "Our 12-session package is R1,680.",
      "approval_status": "sent"
    }
    ```

### 7. Approval and Failure Rules
*   **Operator Rejection Rule:** If the studio staff enters `n` at the prompt, the draft is immediately discarded, and a state record of `"rejected"` is written to the execution history.
*   **Data Deficit (Escalation Rule):** If a user query targets items missing from the file (e.g., *"Do you have a 20-session pack?"*), the system forces the fallback phrase. A status of `"sent"` can only be logged for this message if the operator actively inputs `y` to approve dispatching the fallback notification.
*   **Schema Breach Rule:** If the downstream AI text pipeline emits malformed or un-parsable JSON structures violating the Pydantic type check, the system must trigger an internal exception layout, skip the approval prompt completely, and record a `"failed_validation"` marker.
*   **API Outage Rule:** Upon encountering network drops, response timeouts, or validation code exceptions from Google AI Studio services, the engine must safely exit execution loops without writing a `"sent"` configuration state.

### 8. Measurable Acceptance Criteria
*   **AC-01 (Strict Grounding Test):** Given a customer query regarding a package size or time option not explicitly declared within the storage database, the system produces the exact string *"I'll check with the owner and come back to you."* without any structural variance or extra text additions.
*   **AC-02 (Operator Interception Integrity):** Given a fully valid enquiry draft where the staff operator responds with `n`, checking the resultant tracking index verifies that `status_log.json` holds no `"sent"` updates for that transaction.
*   **AC-03 (Pydantic Resiliency Mock):** Given an intentionally modified or broken mock AI return payload that deletes requested parameter schemas, running the script must throw a catchable operational error flag instead of passing raw string segments directly to the console.

### 9. Ambiguities and Assumptions
*   **Ambiguity 1 (Multi-intent Queries):** The brief does not explicitly define how the draft should be combined if a customer query addresses *both* a package price and an availability slot in a single string.
    *   *Our Assumption:* The Pydantic model will capture arrays/lists of details, and the local lookup function will concatenate the facts into a unified draft response (e.g., *"Our 12-session pack is R1,680. Regarding Saturday availability, 09:00 is Available."*).
*   **Ambiguity 2 (Currency formatting):** The brief specifies raw data numbers (e.g., `R1,680`) but does not explicitly designate whether drafts should display formalized Rand monetary structures or match the exact text style of the database input.
    *   *Our Assumption:* Output generation logic will automatically standardize all pricing fields with a prefix character of `"R"` and comma groupings to ensure uniform presentation quality for South African clientele.
