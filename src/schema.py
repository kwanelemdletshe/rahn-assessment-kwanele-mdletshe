from pydantic import BaseModel, Field
from typing import Optional


class EnquiryAnalysis(BaseModel):
    intent: str = Field(
        description="The primary category of enquiry. Must be one of: 'package_enquiry', 'availability_enquiry', 'mixed_enquiry', or 'unknown'."
    )
    extracted_package_type: Optional[str] = Field(
        description="Extracted package keyword requested by user. Must strictly map to: 'single_session', '5_sessions', or '12_sessions'. If not mentioned, return null."
    )
    extracted_time_slot: Optional[str] = Field(
        description="Extracted target time slot requested by user in exact HH:MM format (e.g., '09:00', '10:00', '11:00'). If not mentioned, return null."
    )
    requires_human_approval: bool = Field(
        description="Mandatory flag. Set this field to true under all circumstances."
    )
