import os
import datetime
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import our custom structural validation and database access handlers
from src.schema import EnquiryAnalysis
from src.database import compile_grounded_response, FALLBACK_ESCALATION_PHRASE

# Load workspace secret variables from the localized environment profile (.env)
load_dotenv()


def initialize_gemini_client() -> genai.Client:
    """
    Initializes and fetches an active authentic Google GenAI client instance with a strict timeout limit.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "CRITICAL: GEMINI_API_KEY missing from environment runtime variables. "
            "Please check your local `.env` configuration file."
        )
    # Set a strict 60-second network connection timeout to kill infinite loops
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))


def analyze_query_with_llm(client: genai.Client, query_string: str) -> EnquiryAnalysis:
    """
    Passes raw input text to Gemini and forces a structured JSON response
    that strictly satisfies our default-free Pydantic validation schema definitions.
    """
    prompt_guidelines = (
        f"Analyze the following incoming customer fitness enquiry: '{query_string}'. "
        "Extract intent categories ('package_enquiry', 'availability_enquiry', 'mixed_enquiry', or 'unknown'). "
        "Map mentioned packages to keys ('single_session', '5_sessions', '12_sessions') and slots to HH:MM format."
    )

    # Use standard stable production model gemini-3.6-flash for high availability
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt_guidelines,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EnquiryAnalysis,
            temperature=0.0,
        ),
    )

    return EnquiryAnalysis.model_validate_json(response.text)


def write_to_status_log(
    query: str,
    analysis: EnquiryAnalysis,
    draft: str,
    status: str,
    log_path: str = "status_log.json",
):
    """
    Appends an auditable record of the interaction to a centralized state ledger.
    """
    log_payload = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "customer_query": query,
        "extracted_intent": analysis.intent,
        "extracted_package": analysis.extracted_package_type,
        "extracted_slot": analysis.extracted_time_slot,
        "generated_draft": draft,
        "approval_status": status,
    }

    log_history = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as file:
                log_history = json.load(file)
                if not isinstance(log_history, list):
                    log_history = []
        except json.JSONDecodeError:
            log_history = []

    log_history.append(log_payload)

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(log_history, file, indent=2)


def main():
    """
    Main orchestration loop mapping out data ingestion, reasoning validation,
    deterministic grounding verification and human verification gating rules.
    """
    print("\nFitDesk AI Enquiry Assistant Initialized.")
    print("--------------------------------------------------")

    customer_query = input("Enter customer enquiry text:\n> ").strip()
    if not customer_query:
        print("Error: Query text cannot be completely empty.")
        return

    try:
        client = initialize_gemini_client()
        print("\nProcessing intent analysis via Gemini API structures...")
        analysis = analyze_query_with_llm(client, customer_query)

        response_draft = compile_grounded_response(
            intent=analysis.intent,
            package_type=analysis.extracted_package_type,
            time_slot=analysis.extracted_time_slot,
        )

        print("\n--- Compiled Response Draft ---")
        print(f'"{response_draft}"')
        print("--------------------------------")

        staff_choice = input("Send draft? (y/n): ").strip().lower()

        # FIX: Only call write_to_status_log if staff enters 'y'
        if staff_choice == "y":
            write_to_status_log(customer_query, analysis, response_draft, "sent")
            print("Operational clearance received. Transaction logged as 'sent'.")
        else:
            # Rejections are intercepted in memory and NOT recorded to the file
            print("Draft intercepted and rejected by operator. Transaction discarded.")

    except Exception as error:
        # FIX: System failures, timeouts, and Pydantic validation errors are printed but never logged to file
        print(f"\nSystem Error Encountered: {error}")
        print("Action aborted due to system/parsing error. Transaction discarded.")


if __name__ == "__main__":
    main()
