# FitDesk Enquiry Assistant
### RAHN Agentic AI Internship — January 2027 Intake At-Home Technical Assessment

**Time Spent on Assessment:** 4 Hours 40 minutes 

This repository contains a lightweight, command-line AI assistant designed for a small fitness studio in Hermanus. It helps staff manage inbound customer enquiries regarding session packages and Saturday availability safely, securely, and with zero factual hallucinations.

The application is engineered strictly to the **RAHN Mandatory Framework for Intern Execution**, decoupling LLM reasoning from local authorized lookups and enforcing a mandatory Human-in-the-Loop approval gate before any action is finalized.

---

##  Repository Structure

```text
rahn-assessment-kwanele-mdletshe/
│
├── docs/
│   ├── SRS.md                      # Mini Software Requirements Specification
│   ├── ARCHITECTURE.md             # Software Architecture Design Document
│   ├── BACKLOG.md                  # Copilot-Friendly Task Breakdown Backlog
│   └── REGRESSION_TESTS.md         # Full Manual & Automated Test Matrix
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # Main application orchestration & CLI loop
│   ├── schema.py                   # Pydantic structured output models
│   └── database.py                 # Local JSON authorized data lookups handler
│
├── tests/
│   ├── __init__.py
│   └── test_assistant.py           # Automated unit tests using pytest & unittest.mock
│
├── data/
│   └── data.json                   # Authorized package pricing and availability data
│
├── status_log.json                 # System activity transaction log (generated at runtime)
├── .env.example                    # Template environment variables configuration
├── .gitignore                      # Prevents .env and runtime caches from being committed
└── requirements.txt                # Python third-party dependency mappings
```

---

##  Installation & Setup

Follow these steps to set up and execute the application locally:

### 1. Clone the Repository
```bash
git clone https://github.com
cd rahn-assessment-kwanele-mdletshe
```

### 2. Set Up a Virtual Environment
```bash
python -m venv .venv
source venv/bin/activate  # On Windows use: .\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file and populate your Google AI Studio credentials:
```bash
cp .env.example .env
```
Open `.env` in a text editor and add your free Gemini API key:
```text
GEMINI_API_KEY=your_actual_api_key_here
```
*(Note: `.env` is explicitly listed in `.gitignore` to prevent secret leakage to public version control).*

---

##  Running the Application

To start the interactive command-line interface, execute the main module from your terminal:
```bash
python -m src.main
```

### Sample Interaction:
```text
 FitDesk Assistant Initialized.
 Enter customer enquiry: How much is the 12-session pack and do you have Saturday slots?

--- Compiled Response Draft ---
Our 12-session package is R1,680. Regarding Saturday availability, 09:00 and 11:00 are available, while 10:00 is fully booked.

Send? (y/n): y
Response recorded as 'sent' in status_log.json.
```

---

## Testing Protocol

Automated regression tests are built using `pytest` and `unittest.mock`. They isolate logic from the live Gemini API, allowing the suite to run rapidly and successfully **without an active API key or incurring usage costs**.

To execute the automated test suites, run the following command in the root directory:
```bash
pytest
```

To run tests with a detailed diagnostic output coverage report:
```bash
pytest -v
```

---

## AI Use & Tooling Disclosure

*   **AI Tools Utilized:** [e.g., ChatGPT / Claude 3.5 Sonnet / GitHub Copilot].
*   **Application Scope:** Used as an engineering accelerator to structure documentation templates (`SRS.md`, `ARCHITECTURE.md`), draft initial Pydantic schema code syntax blocks, and configure `pytest.mock` boilerplate frameworks.
*   **What Doesn't Work Yet:** *Be completely honest here as per RAHN guidelines. E.g., "The system maps single queries effectively, but multi-sentence compound queries sometimes misclassify partial fields in the Pydantic parser, forcing the fallback mechanism safely."*

---

## Working Style
* **Crucial Rule Reminder:** As per Section 08, Rule 3 of the brief, you must write this section entirely yourself without the use of AI tools. Write between 80 to 150 words per response.*

### 1. It is 22:00, and you have been stuck on the same error for three hours. What do you do next, step by step?
- I would start by comparing the last working commit with the current branch that have an error, if the error is too complex or ambiguis ill just cut it off and start to pull a new branch again so that ill start afresh.
- This time i would write down different styles of approach to tackle this issue if the most appropriate style is not working ill ask for help to my partner or collegue or AI assistence.
- In an AI assistence i would just highlight the bug and prompt it with a feature in that way ill be able to fix an error.

### 2. It is Wednesday. Your teammate has not replied to messages since Monday, and you present together on Friday. What do you do?
- Sending an email to our project lead to make an update so that s\he would know abput an issue maybe s\he will be able to cantact teammate.
- I would start completing everything by myself if its possable ill make sure i understand everything on our project and try to complete what can be completed in that short period of time.
- I would start preparing to pressent everything since ill be responsable for that, so understanding everything will help me even if i didnt complete coding.

### 3. Your mentor tells you that the approach you have spent two days on is wrong. How do you react, and what do you do next?
- i would just politly ask that is it a feature that is wrong, maybe i didnt make it right, or the project owner doesnt want that feature anymore. 
- if the feature is not required anymore ill just ask for a new one to work on before the time is due.
- If the problem is that i didnt make it well ill ask where did i make it wrong or what exacly the feature should do.
- if that feature is wrong ill just drop it ask a right one.

### 4. From January to March 2027, you must attend sessions every Monday, Wednesday and Friday. What in your life could get in the way, and what is your plan for each thing?
- Ill manage to since im currently unemployed ill have full time doing whats required from me, even if i get a job during this internship i think i can manage to do what required from me i can work under pressure even on weekends i can push to complete the task but if i get a new job during this iternship ill send an email to let RAHN know about my current employment status.
- Ill attend every session not unless theres an issue but youll know if theres an issue.