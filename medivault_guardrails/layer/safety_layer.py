"""
Clinical Safety Layer Orchestrator for MediVault AI.

Coordinates the Prompt Shield, Clinical Risk Classifier, and Output Filter
to enforce zero-tolerance medical safety guardrails across the platform.
"""
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timezone
import logging

from medivault_guardrails.schemas.guardrail_schema import (
    RiskCategory,
    RiskLevel,
    GuardrailAction,
    InputCheckRequest,
    InputCheckResponse,
    OutputCheckRequest,
    OutputCheckResponse,
    SafetyProcessRequest,
    SafetyProcessResponse,
    STANDARD_SAFETY_RESPONSE,
    EMERGENCY_SAFETY_RESPONSE,
)
from medivault_guardrails.shields.prompt_shield import MedicalPromptShield
from medivault_guardrails.classifier.risk_classifier import ClinicalRiskClassifier
from medivault_guardrails.filters.output_filter import MedicalOutputFilter

logger = logging.getLogger("medivault.guardrails")

class ClinicalSafetyLayer:
    """
    Unified Medical AI Guardrail Orchestrator.
    Guarantees that user queries and model answers strictly adhere to educational boundaries.
    """

    def __init__(
        self,
        prompt_shield: Optional[MedicalPromptShield] = None,
        risk_classifier: Optional[ClinicalRiskClassifier] = None,
        output_filter: Optional[MedicalOutputFilter] = None,
    ):
        self.prompt_shield = prompt_shield or MedicalPromptShield()
        self.risk_classifier = risk_classifier or ClinicalRiskClassifier()
        self.output_filter = output_filter or MedicalOutputFilter()

    def check_input(self, request: InputCheckRequest) -> InputCheckResponse:
        """
        Step 1: Inspect input through Prompt Shield and Clinical Risk Classifier.
        """
        query = request.query.strip()

        # 1. Run Prompt Shield (jailbreak, injection, adversarial evasion)
        shield_res = self.prompt_shield.inspect(query)
        if not shield_res.is_safe:
            return InputCheckResponse(
                query=query,
                action=GuardrailAction.BLOCK,
                is_allowed=False,
                risk_classification=self.risk_classifier.classify_query(query),
                prompt_shield=shield_res,
                safe_response=STANDARD_SAFETY_RESPONSE,
            )

        # 2. Run Clinical Risk Classifier (diagnosis solicitation, prescribing, dosing, emergencies)
        class_res = self.risk_classifier.classify_query(shield_res.sanitized_prompt or query)
        if not class_res.is_allowed:
            return InputCheckResponse(
                query=query,
                action=class_res.recommended_action,
                is_allowed=False,
                risk_classification=class_res,
                prompt_shield=shield_res,
                safe_response=class_res.refusal_message or STANDARD_SAFETY_RESPONSE,
            )

        # Input is verified safe educational inquiry
        return InputCheckResponse(
            query=query,
            action=GuardrailAction.ALLOW,
            is_allowed=True,
            risk_classification=class_res,
            prompt_shield=shield_res,
            safe_response=None,
        )

    def check_output(self, request: OutputCheckRequest) -> OutputCheckResponse:
        """
        Step 2: Inspect generated response through Medical Output Filter.
        """
        filter_res = self.output_filter.filter_output(request.text)
        return OutputCheckResponse(
            is_clean=filter_res.is_clean,
            action=filter_res.action_taken,
            forbidden_matches=filter_res.forbidden_matches,
            final_text=filter_res.filtered_text,
            audit_notes=filter_res.audit_notes,
        )

    def process(
        self,
        request: SafetyProcessRequest,
        generator_fn: Optional[Callable[[str], str]] = None,
    ) -> SafetyProcessResponse:
        """
        Step 3: End-to-end execution.
        Evaluates input -> executes generation if allowed -> filters and sanitizes output.
        """
        input_req = InputCheckRequest(
            query=request.query,
            patient_id=request.patient_id,
            metadata=request.metadata,
        )
        input_eval = self.check_input(input_req)

        # If input violates clinical safety rules, reject immediately without generation
        if not input_eval.is_allowed:
            return SafetyProcessResponse(
                query=request.query,
                input_status=input_eval.action,
                is_blocked=True,
                final_output=input_eval.safe_response or STANDARD_SAFETY_RESPONSE,
                risk_category=input_eval.risk_classification.category,
                risk_level=input_eval.risk_classification.risk_level,
                audit_trail={
                    "stage": "INPUT_SHIELD",
                    "action": input_eval.action.value,
                    "matched_patterns": input_eval.risk_classification.matched_patterns,
                    "shield_rules": input_eval.prompt_shield.triggered_rules,
                },
            )

        # Input is allowed: execute generation function (or return educational clearance)
        raw_output = ""
        if generator_fn is not None:
            raw_output = generator_fn(request.query)
        else:
            raw_output = (
                f"Educational analysis for query: '{request.query}'. "
                "The findings are within clinical bounds and require professional consultation."
            )

        # Inspect generated output through Output Filter
        output_req = OutputCheckRequest(
            text=raw_output,
            query_context=request.query,
            patient_id=request.patient_id,
        )
        output_eval = self.check_output(output_req)

        return SafetyProcessResponse(
            query=request.query,
            input_status=input_eval.action,
            is_blocked=not output_eval.is_clean,
            final_output=output_eval.final_text,
            risk_category=input_eval.risk_classification.category,
            risk_level=input_eval.risk_classification.risk_level,
            audit_trail={
                "stage": "OUTPUT_FILTER" if not output_eval.is_clean else "COMPLETED_CLEAN",
                "action": output_eval.action.value,
                "forbidden_output_matches": output_eval.forbidden_matches,
                "notes": output_eval.audit_notes,
            },
        )
