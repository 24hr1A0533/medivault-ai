"""
Pydantic schemas and constants for MediVault Medical AI Safety Guardrails.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

STANDARD_SAFETY_RESPONSE = "This information is educational only. Please consult a licensed healthcare professional."
EMERGENCY_SAFETY_RESPONSE = "This may indicate a medical emergency. Please call emergency services (911 or your local emergency number) or go to the nearest emergency room immediately."

class RiskCategory(str, Enum):
    SAFE_EDUCATIONAL = "SAFE_EDUCATIONAL"
    DIAGNOSIS_SOLICITATION = "DIAGNOSIS_SOLICITATION"
    PRESCRIPTION_REQUEST = "PRESCRIPTION_REQUEST"
    DOSAGE_ALTERATION = "DOSAGE_ALTERATION"
    TREATMENT_PLAN = "TREATMENT_PLAN"
    DOCTOR_REPLACEMENT = "DOCTOR_REPLACEMENT"
    EMERGENCY_TRIAGE = "EMERGENCY_TRIAGE"
    ADVERSARIAL_INJECTION = "ADVERSARIAL_INJECTION"

class RiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GuardrailAction(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    SANITIZE = "SANITIZE"
    ESCALATE_EMERGENCY = "ESCALATE_EMERGENCY"

class PromptShieldResult(BaseModel):
    is_safe: bool = Field(..., description="Whether prompt passed all injection and safety shields")
    risk_category: RiskCategory = Field(default=RiskCategory.SAFE_EDUCATIONAL)
    risk_level: RiskLevel = Field(default=RiskLevel.NONE)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    triggered_rules: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    sanitized_prompt: Optional[str] = None

class RiskClassificationResult(BaseModel):
    category: RiskCategory
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=1.0)
    matched_patterns: List[str] = Field(default_factory=list)
    is_allowed: bool
    recommended_action: GuardrailAction
    refusal_message: Optional[str] = None

class OutputFilterResult(BaseModel):
    is_clean: bool = Field(..., description="True if no forbidden diagnostic/prescriptive phrases exist")
    action_taken: GuardrailAction
    forbidden_matches: List[str] = Field(default_factory=list)
    original_text: str
    filtered_text: str
    audit_notes: List[str] = Field(default_factory=list)

class InputCheckRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User prompt or question to evaluate")
    patient_id: Optional[str] = Field(default=None, description="Optional patient ID context")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InputCheckResponse(BaseModel):
    query: str
    action: GuardrailAction
    is_allowed: bool
    risk_classification: RiskClassificationResult
    prompt_shield: PromptShieldResult
    safe_response: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OutputCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw model generated text to check")
    query_context: Optional[str] = Field(default=None, description="Original user prompt")
    patient_id: Optional[str] = Field(default=None)

class OutputCheckResponse(BaseModel):
    is_clean: bool
    action: GuardrailAction
    forbidden_matches: List[str]
    final_text: str
    audit_notes: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SafetyProcessRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User prompt")
    patient_id: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SafetyProcessResponse(BaseModel):
    query: str
    input_status: GuardrailAction
    is_blocked: bool
    final_output: str
    risk_category: RiskCategory
    risk_level: RiskLevel
    audit_trail: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
