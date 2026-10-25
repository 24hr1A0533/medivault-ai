"""
Dataset Pipeline for Healthcare LLM Fine-Tuning.
Ingests, normalizes, formats, and tokenizes samples from MIMIC-IV, PubMedQA, MedQA, and MedMCQA.
"""
import random
from typing import List, Dict, Any, Tuple, Optional
from medivault_healthcare_llm.dataset.data_schema import (
    MedicalTaskType,
    ChatMessage,
    MedicalTrainingSample,
)

SYSTEM_PROMPT = (
    "You are MediVault Clinical AI, an expert medical intelligence system. "
    "Provide medically accurate, source-grounded, and patient-safe explanations. "
    "Adhere strictly to clinical evidence without inventing laboratory values. "
    "When explaining reports or answering clinical queries, state relevant reference ranges "
    "and cite corresponding document sources. Note that your advice is educational and supports "
    "rather than replaces licensed physician judgment."
)

class HealthcareDatasetPipeline:
    """
    Standardizes raw medical benchmark datasets into ChatML training sequences.
    """

    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        self.system_prompt = system_prompt

    def transform_mimic_iv_sample(
        self,
        sample_id: str,
        discharge_summary_text: str,
        target_explanation: str,
        domain: str = "Inpatient / Critical Care",
    ) -> MedicalTrainingSample:
        """
        Transforms a MIMIC-IV clinical report into an explanation / summary instruction pair.
        """
        user_prompt = (
            f"Please analyze this clinical discharge summary and explain the patient's hospital course, "
            f"key diagnostic findings, and discharge recommendations in clear clinical terms:\n\n"
            f"```clinical_record\n{discharge_summary_text.strip()}\n```"
        )
        return MedicalTrainingSample(
            id=f"MIMIC-{sample_id}",
            dataset_source="MIMIC-IV",
            task_type=MedicalTaskType.REPORT_EXPLANATION,
            messages=[
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=user_prompt),
                ChatMessage(role="assistant", content=target_explanation.strip()),
            ],
            clinical_domain=domain,
            citation_sources=["MIMIC-IV Clinical Database"],
        )

    def transform_pubmedqa_sample(
        self,
        sample_id: str,
        question: str,
        abstract_context: str,
        answer: str,
        domain: str = "Biomedical Literature",
    ) -> MedicalTrainingSample:
        """
        Transforms a PubMedQA abstract + question into a RAG answering training pair.
        """
        user_prompt = (
            f"Based strictly on the provided biomedical literature abstract, answer the research question "
            f"and explain the underlying physiological or pharmacological mechanism:\n\n"
            f"EVIDENCE CONTEXT:\n{abstract_context.strip()}\n\n"
            f"QUESTION: {question.strip()}"
        )
        return MedicalTrainingSample(
            id=f"PUBMED-{sample_id}",
            dataset_source="PubMedQA",
            task_type=MedicalTaskType.RAG_ANSWERING,
            messages=[
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=user_prompt),
                ChatMessage(role="assistant", content=answer.strip()),
            ],
            clinical_domain=domain,
            citation_sources=["PubMed Central Biomedical Archive"],
        )

    def transform_medqa_sample(
        self,
        sample_id: str,
        clinical_case_vignette: str,
        options: Dict[str, str],
        correct_answer: str,
        clinical_rationale: str,
        domain: str = "USMLE Clinical Decision",
    ) -> MedicalTrainingSample:
        """
        Transforms a MedQA case vignette into a clinical reasoning & decision-making pair.
        """
        opts_formatted = "\n".join([f"{k}: {v}" for k, v in options.items()])
        user_prompt = (
            f"Evaluate this clinical case vignette, determine the most likely diagnosis or management step, "
            f"and justify the underlying pathophysiological reasoning:\n\n"
            f"CASE VIGNETTE:\n{clinical_case_vignette.strip()}\n\n"
            f"OPTIONS:\n{opts_formatted}"
        )
        assistant_reply = (
            f"Correct Answer: {correct_answer}\n\n"
            f"Clinical Rationale:\n{clinical_rationale.strip()}"
        )
        return MedicalTrainingSample(
            id=f"MEDQA-{sample_id}",
            dataset_source="MedQA",
            task_type=MedicalTaskType.CLINICAL_DECISION_SUPPORT,
            messages=[
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=user_prompt),
                ChatMessage(role="assistant", content=assistant_reply),
            ],
            clinical_domain=domain,
            citation_sources=["MedQA / USMLE Clinical Vignette Repository"],
        )

    def transform_medmcqa_sample(
        self,
        sample_id: str,
        concept_term_or_question: str,
        detailed_explanation: str,
        specialty: str = "Pharmacology",
    ) -> MedicalTrainingSample:
        """
        Transforms a MedMCQA terminology item into a medical terminology understanding pair.
        """
        user_prompt = (
            f"Explain the clinical terminology, pharmacological properties, and diagnostic relevance of the following topic:\n\n"
            f"TOPIC / CONCEPT: {concept_term_or_question.strip()}"
        )
        return MedicalTrainingSample(
            id=f"MEDMCQA-{sample_id}",
            dataset_source="MedMCQA",
            task_type=MedicalTaskType.TERMINOLOGY_UNDERSTANDING,
            messages=[
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=user_prompt),
                ChatMessage(role="assistant", content=detailed_explanation.strip()),
            ],
            clinical_domain=specialty,
            citation_sources=["MedMCQA Specialty Examination Dataset"],
        )

    def mix_and_split(
        self,
        samples: List[MedicalTrainingSample],
        train_ratio: float = 0.9,
        seed: int = 42,
    ) -> Tuple[List[MedicalTrainingSample], List[MedicalTrainingSample]]:
        """
        Shuffles and stratifies dataset mixture into train and validation splits.
        """
        rng = random.Random(seed)
        shuffled = list(samples)
        rng.shuffle(shuffled)

        split_idx = int(len(shuffled) * train_ratio)
        train_set = shuffled[:split_idx]
        val_set = shuffled[split_idx:]
        return train_set, val_set
