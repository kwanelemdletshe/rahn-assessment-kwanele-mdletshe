import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Import components from our source workspace modules
from src.schema import EnquiryAnalysis
from src.database import compile_grounded_response, FALLBACK_ESCALATION_PHRASE
from src.main import analyze_query_with_llm, write_to_status_log


@pytest.fixture
def mock_db_file(tmp_path):
    """
    Fixture to create a temporary, controlled data.json file
    to insulate regression tests from shifts in working production databases.
    """
    mock_facts = {
        "packages": {
            "single_session": "R180",
            "5_sessions": "R800",
            "12_sessions": "R1,680",
        },
        "saturday_availability": {
            "09:00": "Available",
            "10:00": "Full",
            "11:00": "Available",
        },
    }
    db_file = tmp_path / "test_data.json"
    db_file.write_text(json.dumps(mock_facts))
    return str(db_file)


@pytest.fixture
def mock_log_file(tmp_path):
    """
    Fixture to provision a temporary isolated logging output file
    to verify audit trail behaviors without clobbering production metrics.
    """
    log_file = tmp_path / "test_status_log.json"
    return str(log_file)


# ============================================================================
# REGRESSION TEST SUITE (Covers requirement metrics defined in REGRESSION_TESTS.md)
# ============================================================================


def test_regression_tr_01_normal_grounded_lookup(mock_db_file):
    """
    TR-01 / FR-03: Verifies that a normal enquiry matching authorized keys
    extracts correct values and builds a fully factual response string.
    """
    draft = compile_grounded_response(
        intent="mixed_enquiry",
        package_type="12_sessions",
        time_slot="09:00",
        db_path=mock_db_file,
    )

    # Assertions updated to match the dynamically generated output vocabulary
    assert "R1,680" in draft
    assert "09:00" in draft
    assert "available" in draft.lower()
    assert draft != FALLBACK_ESCALATION_PHRASE


def test_regression_tr_02_fact_deficit_escalation(mock_db_file):
    """
    TR-02 / FR-04 / AC-01: Verifies that a query regarding a missing or unauthorized
    package parameter triggers the exact non-negotiable fallback string instead of guessing.
    """
    draft = compile_grounded_response(
        intent="package_enquiry",
        package_type="20_sessions",  # Missing item type
        time_slot=None,
        db_path=mock_db_file,
    )

    assert draft == FALLBACK_ESCALATION_PHRASE


def test_regression_tr_03_pydantic_schema_enforcement():
    """
    TR-03 / FR-02: Assures the system validation loop blocks invalid, corrupted,
    or un-parsable downstream AI response strings using strict Pydantic model limits.
    """
    invalid_json_payload = (
        '{"intent": "package_enquiry", "extracted_package_type":'  # Corrupted syntax
    )

    with pytest.raises(Exception):
        # Shifting raw broken strings into the model-validator framework must fail cleanly
        EnquiryAnalysis.model_validate_json(invalid_json_payload)


@patch("google.genai.Client")
def test_regression_tr_04_api_client_error_handling(mock_client_class):
    """
    TR-04 / NFR-01: Verifies that network drops or server timeouts on the
    upstream third-party API surface exit gracefully.
    """
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Simulate a network/timeout outage crash directly on the generation method
    mock_client.models.generate_content.side_effect = Exception(
        "API connection timed out."
    )

    with pytest.raises(Exception) as error_context:
        analyze_query_with_llm(mock_client, "Hello, can you help me?")

    assert "API connection timed out" in str(error_context.value)


def test_regression_tr_05_manual_operator_rejection(mock_log_file):
    """
    TR-05 / FR-05 / AC-02: Proves that when human operators select 'n' (No)
    at the terminal validation step, transactions are classified as 'rejected'.
    """
    # FIX: Explicitly supply all attributes to pass Pydantic validation
    mock_analysis = EnquiryAnalysis(
        intent="package_enquiry",
        extracted_package_type="single_session",
        extracted_time_slot=None,
        requires_human_approval=True,
    )

    # Run the transaction update simulating manual operator cancellation
    write_to_status_log(
        query="How much is one session?",
        analysis=mock_analysis,
        draft="Our Single session package is R180.",
        status="rejected",
        log_path=mock_log_file,
    )

    with open(mock_log_file, "r", encoding="utf-8") as file:
        logs = json.load(file)

    assert len(logs) == 1
    assert logs[0]["approval_status"] == "rejected"
    assert logs[0]["generated_draft"] == "Our Single session package is R180."


def test_regression_tr_06_manual_operator_approval(mock_log_file):
    """
    TR-06 / FR-05: Assures that when human operators provide operational clearance 'y',
    the interaction maps cleanly onto an auditable 'sent' state trace block.
    """
    # FIX: Explicitly supply all attributes to pass Pydantic validation
    mock_analysis = EnquiryAnalysis(
        intent="package_enquiry",
        extracted_package_type="single_session",
        extracted_time_slot=None,
        requires_human_approval=True,
    )

    write_to_status_log(
        query="How much is one session?",
        analysis=mock_analysis,
        draft="Our Single session package is R180.",
        status="sent",
        log_path=mock_log_file,
    )

    with open(mock_log_file, "r", encoding="utf-8") as file:
        logs = json.load(file)

    assert len(logs) == 1
    assert logs[0]["approval_status"] == "sent"
