"""
Data schemas for Medical LLM Training Dataset.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MedicalTaskType(str, Enum):
    REPORT_EXPLANATION = "REPORT_EXPLANATION"
    RAG_ANSWERING = "RAG_ANSWERING"
    TERMINOLOGY_UNDERSTANDING = "TERMINOLOGY_UNDERSTANDING"
    CLINICAL_DECISION_SUPPORT = "CLINICAL_DECISION_SUPPORT"
    DOCTOR_SUMMARY = "DOCTOR_SUMMARY"

class ChatMessage(BaseModel):
    role: str = Field(..., description="'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message text content")

class MedicalTrainingSample(BaseModel):
    id: str
    dataset_source: str = Field(..., description="'MIMIC-IV', 'PubMedQA', 'MedQA', 'MedMCQA'")
    task_type: MedicalTaskType
    messages: List[ChatMessage]
    clinical_domain: str = Field(default="General Medicine")
    citation_sources: Optional[List[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_chatml(self) -> str:
        """
        Formats sample into ChatML prompt string.
        """
        formatted = []
        for msg in self.messages:
            formatted.append(f"<|im_start|>{msg.role}\n{msg.content.strip()}<|im_end|>")
        return "\n".join(formatted)
