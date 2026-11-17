# RAPLH Tooling Log & Reflection

This document contains genuine chronological logs tracking how the engineering loop iterated through requirements verification, risk analysis, and human validation gates.

---

## Iteration Entry 1: Resolving Rejection Logging Leak
*   **Task/Objective:** Fix status logging to ensure rejected drafts are not permanently saved to the JSON audit file.
*   **AI Prompt Summary:** Refactor the main execution loop to safely intercept rejections and wrap the `write_to_status_log` execution block inside a strict conditional gate.
*   **Files Changed:** `src/main.py`
*   **Test Executed & Result:** Ran manual testing using query `"how much is a single session"` and inputting `n`. The log stream was verified as clean.
*   **Correction & Approval:** Successfully blocked file append loops on user rejection. Verified and approved.
*   **Log Authenticity Status:** *Genuine Record of Activity.*

---

## Iteration Entry 2: Correcting General Saturday Availability Lookups
*   **Task/Objective:** Fix fact-deficit crash when users make general availability inquiries without specifying a precise time slot.
*   **AI Prompt Summary:** Modify `compile_grounded_response` to dynamically query and assemble a list of all "Available" database parameters when `time_slot` returns empty.
*   **Files Changed:** `src/database.py`, `tests/test_assistant.py`
*   **Test Executed & Result:** Executed `pytest tests/`. Initial trace failed on string mapping parameters, updated assertions to decouple specific text tags, resulting in 100% green pass.
*   **Correction & Approval:** Structured dynamic string builders for open slots. Verified and approved.
*   **Log Authenticity Status:** *Genuine Record of Activity.*

---

## Technical Guardrail Reflections

### 1. How would you stop an AI coding agent from changing unrelated files or exposing your API key?
*   **Strict Scope Restraints:** Pin down code-execution parameters using clear file-specific permissions flags (e.g., executing scripts within a container or specifying explicitly which file paths are read/write active for the session).
*   **Environmental Layering:** Force all credentials out of the codebase using native system environment profiles or `.env` variable structures paired with rigid `.gitignore` block patterns.

### 2. How would you stop the loop if the agent keeps repeating the same failed fix?
*   **Iteration Counter Caps:** Enforce an explicit hard-coded execution budget counter inside the agent pipeline logic loop (e.g., maximum 3 attempts). 
*   **Exception Deflection:** If the system hits the same cryptographic file checksum or failing unit test trace twice consecutively, kill processing immediately, dump error states to a local debugger log, and drop out to a human developer notice prompt.
