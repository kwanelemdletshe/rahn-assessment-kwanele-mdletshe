import os
import json
from typing import Dict, Any, Optional

# Global constant defining the exact fallback phrase required by the business brief.
# If any requested piece of data is missing, the assistant must never guess.
FALLBACK_ESCALATION_PHRASE = "I'll check with the owner and come back to you."


def load_authorized_facts(file_path: str = "data/data.json") -> Dict[str, Any]:
    """
    Loads the approved studio price list and availability map from a local JSON file.

    Args:
        file_path (str): Relative path to the authorized facts database file.

    Returns:
        Dict[str, Any]: A nested dictionary containing 'packages' and 'saturday_availability'.
    """
    # Enforce safe execution fallback if the file doesn't exist yet
    if not os.path.exists(file_path):
        return {"packages": {}, "saturday_availability": {}}

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def compile_grounded_response(
    intent: str,
    package_type: Optional[str] = None,
    time_slot: Optional[str] = None,
    db_path: str = "data/data.json",
) -> str:
    """
    Evaluates extracted query parameters against local authorized studio facts.
    Applies strict business logic rules to compile a response or escalate.

    Args:
        intent (str): The categorized customer intent ('package_enquiry', 'availability_enquiry', etc.)
        package_type (str, optional): Target key extracted by the AI (e.g., '12_sessions').
        time_slot (str, optional): Target slot string extracted by the AI (e.g., '10:00').
        db_path (str): Overridable database path primarily used for isolated testing hooks.

    Returns:
        str: A deterministic string draft or the exact required escalation fallback phrase.
    """
    # Load the ground-truth studio data file
    facts = load_authorized_facts(db_path)
    packages_db = facts.get("packages", {})
    availability_db = facts.get("saturday_availability", {})

    # Store dynamic text fragments for compilation
    response_parts = []

    # RULE EVALUATION PATH 1: Handle Package/Pricing Queries
    if intent in ["package_enquiry", "mixed_enquiry"] or package_type is not None:
        # Check if the extracted package exists within our authorized database keys
        if package_type and package_type in packages_db:
            price = packages_db[package_type]
            # Format clean, user-friendly labels out of snake_case parameter structures
            clean_name = package_type.replace("_", " ").capitalize()
            response_parts.append(f"Our {clean_name} package is {price}.")
        else:
            # FACT DEFICIT: The AI extracted a package option that isn't in our file.
            # Enforce the non-negotiable escalation rule immediately.
            return FALLBACK_ESCALATION_PHRASE

    # RULE EVALUATION PATH 2: Handle Saturday Availability Queries
    if intent in ["availability_enquiry", "mixed_enquiry"] or time_slot is not None:
        if time_slot:
            # Case A: User asked about a specific time slot (e.g., "Is 09:00 open?")
            if time_slot in availability_db:
                status = availability_db[time_slot]
                response_parts.append(
                    f"Regarding Saturday availability, the {time_slot} slot is currently {status.lower()}."
                )
            else:
                # FACT DEFICIT: The user asked for a time slot outside our recorded hours.
                return FALLBACK_ESCALATION_PHRASE
        else:
            # Case B: General availability enquiry (e.g., "What times are available on Saturday?")
            # Filter and gather all time slots that have a value of "Available"
            open_slots = [
                slot
                for slot, status in availability_db.items()
                if status.lower() == "available"
            ]

            if open_slots:
                # Format a friendly list (e.g., "09:00 and 11:00")
                slots_str = (
                    ", ".join(open_slots[:-1]) + f" and {open_slots[-1]}"
                    if len(open_slots) > 1
                    else open_slots[0]
                )
                response_parts.append(
                    f"On Saturday, the available slots are {slots_str}."
                )
            else:
                response_parts.append("We are fully booked this Saturday.")

    # GUARD CLAUSE: Handle unknown or unmappable conversational inputs safely
    if not response_parts:
        return FALLBACK_ESCALATION_PHRASE

    # Join the evaluated, grounded data sentences together into a clean response draft
    return " ".join(response_parts)
