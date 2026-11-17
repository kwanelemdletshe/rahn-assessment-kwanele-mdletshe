import os
import datetime
import json
import time  # Added to manage retry delays under server spikes
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

    # FIX: Fall back to standard stable production model if variable is missing or blank
    env_model = os.getenv("GEMINI_MODEL")
    configured_model = (
        env_model.strip() if env_model and env_model.strip() else "gemini-2.5-flash"
    )

    response = client.models.generate_content(
        model=configured_model,
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

    # Configuration for automatic self-healing resilience loop
    max_retries = 3
    retry_delay = 2  # seconds
    analysis = None

    # Step 1: Run the LLM analysis with built-in infrastructure timeout/congested retries
    for attempt in range(max_retries):
        try:
            client = initialize_gemini_client()

            # Print execution attempt path tracking metrics
            attempt_suffix = (
                f" (Attempt {attempt + 1}/{max_retries})" if attempt > 0 else ""
            )
            print(
                f"\nProcessing intent analysis via Gemini API structures...{attempt_suffix}"
            )

            analysis = analyze_query_with_llm(client, customer_query)
            break  # Break out cleanly if the network request succeeds

        except Exception as error:
            error_str = str(error)
            # Intercept known server congestion codes (503 High Demand / 504 Timeout) to retry safely
            if (
                "503" in error_str
                or "504" in error_str
                or "deadline_exceeded" in error_str.lower()
            ):
                if attempt < max_retries - 1:
                    print(
                        f"Temporary server congestion encountered. Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                    continue

            # Raise the exception to the final fallback block if it's permanent or out of retries
            print(f"\nSystem Error Encountered: {error}")
            print("Action aborted due to system/parsing error. Transaction discarded.")
            return

    # Step 2: Ground the validated response parameters and handle human validation gate
    if analysis is not None:
        try:
            response_draft = compile_grounded_response(
                intent=analysis.intent,
                package_type=analysis.extracted_package_type,
                time_slot=analysis.extracted_time_slot,
            )

            print("\n--- Compiled Response Draft ---")
            print(f'"{response_draft}"')
            print("--------------------------------")

            staff_choice = input("Send draft? (y/n): ").strip().lower()

            # Only call write_to_status_log if staff enters 'y'
            if staff_choice == "y":
                write_to_status_log(customer_query, analysis, response_draft, "sent")
                print("Operational clearance received. Transaction logged as 'sent'.")
            else:
                # Rejections are intercepted in memory and NOT recorded to the file
                print(
                    "Draft intercepted and rejected by operator. Transaction discarded."
                )

        except Exception as error:
            print(f"\nSystem Error Encountered during grounding execution: {error}")
            print("Action aborted due to system/parsing error. Transaction discarded.")


if __name__ == "__main__":
    main()
