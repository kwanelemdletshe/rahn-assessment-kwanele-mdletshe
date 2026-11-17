# Test Plan & Regression Matrix
## Project: FitDesk Enquiry Assistant

This document outlines the evaluation criteria used to prove the architectural safety, grounding precision, and error resilience of the application.

### 1. Core Testing Strategy
*   **Decoupled Automation:** To comply with project guidelines, all automated regression suites must run locally without requiring an active Gemini API credential or incurring transaction costs.
*   **Mocks Framework:** The Google Gemini client interface layer is fully intercepted using `unittest.mock`, returning pre-fabricated JSON strings that model specific operational scenarios.
*   **Tracing Verification:** Every test scenario maps directly back to a functional requirement identifier (FR-XX) or non-functional structural limit (NFR-XX) defined within `docs/SRS.md`.

### 2. Full Regression Test Matrix

| Test ID | Targeted Requirement | Scenario / Intent | Input Precondition | Operational Steps | Expected Deterministic Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TR-01** | FR-01, FR-03, FR-06 | Normal lookup with complete data | `"How much is the 12-session pack and do you have Saturday slots?"` | 1. Initialize main script CLI prompt.<br>2. Intercept Gemini output with valid JSON mapping `12_sessions` and `09:00`.<br>3. Trigger local database lookup.<br>4. Enter `y` at approval gate. | • Prints draft containing: `R1,680` and `09:00 Available`.<br>• Appends log entry with state `"sent"`. |
| **TR-02** | FR-04, AC-01 | Fact-deficit / Out-of-bounds parameter | `"Can I book a 20-session package?"` | 1. Supply raw string containing out-of-bounds parameter.<br>2. Model extracts target package.<br>3. Scan data lookup engine.<br>4. Enter `y` at approval gate. | • Generates **exact** phrase: `"I'll check with the owner and come back to you."`<br>• Appends log entry with state `"sent"`. |
| **TR-03** | FR-02, NFR-01, AC-03 | Broken or malformed AI schema response | `"Hello studio!"` | 1. Input arbitrary initialization text.<br>2. Inject corrupted or truncated JSON string directly from mock engine. | • Application throws clean Pydantic processing exception.<br>• Script terminates without prompting user (`y/n`).<br>• Logs operational state `"failed_validation"`. |
| **TR-04** | NFR-01, Approval Rule | Upstream third-party API outage | `"Is 11:00 open?"` | 1. Input valid message string.<br>2. Force mock Gemini client layer to raise a connection timeout or network exception. | • Application catches exception gracefully.<br>• Script terminates immediately before CLI user gate.<br>• No entry written to `status_log.json` with status `"sent"`. |
| **TR-05** | FR-05, AC-02 | Operator manual rejection gate | `"How much is a single session?"` | 1. Input valid query.<br>2. Core extracts valid data (`R180`).<br>3. Halt processing at terminal prompt.<br>4. **Enter `n` at CLI gate.** | • System discards compiled draft.<br>• Writes transactional summary state entry as `"rejected"`. |
| **TR-06** | FR-05, FR-06 | Operator manual validation gate | `"How much is a single session?"` | 1. Input valid query.<br>2. Core extracts valid data (`R180`).<br>3. Halt processing at terminal prompt.<br>4. **Enter `y` at CLI gate.** | • System validates draft output.<br>• Writes transactional summary state entry as `"sent"`. |

### 3. Automated Test Blueprint Template
This snippet outlines how `tests/test_assistant.py` leverages python mocking frameworks to test your application business logic offline.

```python
import pytest
import json
from unittest.mock import patch, MagicMock
from src.schema import EnquiryAnalysis
from src.database import lookup_facts

# Automated Test mapping to TR-01 & TR-06
@patch('google.genai.Client') 
@patch('builtins.input', side_counts=['y'])
def test_normal_flow_with_operator_approval(mock_input, mock_client_class):
    # Setup mock Gemini Response structure
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Simulate valid structural Pydantic delivery return
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "intent": "package_enquiry",
        "extracted_package_type": "12_sessions",
        "extracted_time_slot": "09:00",
        "requires_human_approval": True
    })
    mock_client.models.generate_content.return_value = mock_response
    
    # Execute structural assert matching criteria here...
    assert True 
```
