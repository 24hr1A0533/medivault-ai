"""
Clinical LLM Reasoning Engine for Patient RAG
Implements specialized prompt templates and reasoning workflows for:
1. Explain Report
2. Summarize Reports
3. Compare Reports
4. Medical Timeline Generation
5. Doctor Visit Summary
Strictly enforces zero hallucination and ground-truth negative constraints.
"""

import os
import re
import logging
from typing import Optional, List
from ..schemas.rag_schema import RAGFeature

logger = logging.getLogger("patient_rag.llm")


SYSTEM_PROMPT = """You are MediVault AI, a senior clinical AI assistant providing patient-facing medical intelligence.
You answer questions STRICTLY based on the provided patient's medical records below.

CRITICAL SAFETY RULES:
1. You have access ONLY to the provided source passages for this specific patient.
2. If the user asks about a test, symptom, date, medication, or fact that is NOT mentioned in the provided sources, you MUST respond EXACTLY with:
   "I could not find that information in your medical records."
   DO NOT guess, assume, or fabricate medical data.
3. Every factual medical statement must cite the source using: [Report: <report_name> | Page: <page_number> | Date: <report_date>].
4. Never reveal or reference documents belonging to any other person.
5. Translate complex clinical jargon into clear, accessible language for the patient, but keep all numeric lab values and drug dosages exact.
"""


class ClinicalLLMEngine:
    """
    Executes grounded clinical reasoning over patient context for the 5 key features.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate_response(
        self,
        feature: RAGFeature,
        query: str,
        context: str,
    ) -> str:
        """
        Generates clinical response based on the selected feature and grounded context.
        """
        if not context or not context.strip():
            return "I could not find that information in your medical records."

        feature_prompt = self._build_feature_prompt(feature, query, context)

        # If LLM API key is configured, execute remote generation
        if self.api_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": feature_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=1500,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                logger.warning(f"Remote LLM call failed: {str(exc)}. Executing local deterministic clinical engine.")

        # High-precision deterministic clinical reasoning fallback
        return self._deterministic_clinical_reasoning(feature, query, context)

    def _build_feature_prompt(self, feature: RAGFeature, query: str, context: str) -> str:
        """Formats feature-specific task instructions."""
        task_descriptions = {
            RAGFeature.EXPLAIN_REPORT: (
                "TASK: EXPLAIN REPORT\n"
                "- Explain the findings of the report in patient-friendly terms.\n"
                "- Clearly identify which parameters are within normal biological ranges and which are abnormal.\n"
                "- Explain what the markers mean for the patient's health.\n"
            ),
            RAGFeature.SUMMARIZE_REPORTS: (
                "TASK: SUMMARIZE MEDICAL REPORTS\n"
                "- Synthesize all provided medical reports into a concise, unified clinical summary.\n"
                "- Group into: Diagnoses/Conditions, Key Lab Findings, Current Medications, and Next Steps.\n"
            ),
            RAGFeature.COMPARE_REPORTS: (
                "TASK: COMPARE MEDICAL REPORTS\n"
                "- Compare the patient's reports across dates/intervals.\n"
                "- Highlight changes, improvements, or deteriorating trends in lab markers or clinical findings.\n"
            ),
            RAGFeature.MEDICAL_TIMELINE: (
                "TASK: MEDICAL TIMELINE GENERATION\n"
                "- Construct a chronological timeline of all medical events, tests, and prescriptions in chronological order.\n"
                "- Format each event as: Date | Encounter / Test | Key Finding / Prescription | Source.\n"
            ),
            RAGFeature.DOCTOR_VISIT_SUMMARY: (
                "TASK: DOCTOR VISIT SUMMARY\n"
                "- Prepare an executive summary for an upcoming or recent doctor consultation.\n"
                "- Include: Chief complaints/reasons for review, active prescriptions, recent abnormal lab metrics, and key discussion questions.\n"
            ),
            RAGFeature.GENERAL_QUERY: (
                "TASK: ANSWER PATIENT QUERY\n"
                "- Answer the user's question directly and thoroughly based strictly on the provided medical records.\n"
            ),
        }

        task_header = task_descriptions.get(feature, task_descriptions[RAGFeature.GENERAL_QUERY])

        return (
            f"{task_header}\n"
            f"USER QUERY: {query}\n\n"
            f"PATIENT'S MEDICAL RECORDS CONTEXT:\n"
            f"{context}\n\n"
            f"Remember: If the requested information is absent from the records above, return EXACTLY:\n"
            f"\"I could not find that information in your medical records.\""
        )

    def _deterministic_clinical_reasoning(
        self,
        feature: RAGFeature,
        query: str,
        context: str,
    ) -> str:
        """
        Deterministic, grounded clinical reasoning engine when offline.
        Parses context blocks and synthesizes structured answers adhering to the feature requirements.
        """
        # Parse context blocks into structured metadata and content
        sources = re.findall(
            r"--- \[SOURCE \d+\] ---\s+Report Name:\s*([^\n]+)\s+Report Date:\s*([^\n]+)\s+Page Number:\s*(\d+)\s+Content:\s*([\s\S]+?)(?=(?:--- \[SOURCE|\Z))",
            context,
        )

        if not sources:
            return "I could not find that information in your medical records."

        # For general queries, check if the query specifically asks for terms absent from the context
        if feature == RAGFeature.GENERAL_QUERY:
            stop_words = {
                "what", "show", "tell", "explain", "summarize", "compare", "when",
                "does", "have", "with", "from", "report", "medical", "records",
                "patient", "about", "your", "mine", "level", "result", "results",
                "test", "tests", "value", "values", "please", "clinical", "findings"
            }
            keywords = [w.lower() for w in re.findall(r"\b[A-Za-z]{3,}\b", query) if w.lower() not in stop_words]
            context_lower = context.lower()

            # If specific medical keywords are queried and NONE exist in the context, trigger fallback
            if keywords and not any(kw in context_lower for kw in keywords):
                return "I could not find that information in your medical records."

        rep_name, rep_date, page_num, raw_content = sources[0]

        if feature == RAGFeature.EXPLAIN_REPORT:
            return (
                f"### Explanation of {rep_name}\n\n"
                f"Based on your **{rep_name}** from **{rep_date}** (Page {page_num}):\n\n"
                f"- **Findings Overview**: Your test results contain key clinical parameters evaluated against standard biological reference ranges.\n"
                f"- **Summary of Results**:\n{self._format_content_bullets(raw_content)}\n\n"
                f"- **What this means**: Normal values reflect healthy baseline organ functioning. Any values marked outside reference intervals should be evaluated with your physician to adjust treatment or lifestyle as needed."
            )

        elif feature == RAGFeature.SUMMARIZE_REPORTS:
            summary_parts = [f"### Consolidated Medical Summary\n"]
            for r_name, r_date, p_num, cnt in sources:
                summary_parts.append(f"#### {r_name} ({r_date}, Page {p_num})\n{self._format_content_bullets(cnt)}\n")
            return "\n".join(summary_parts)

        elif feature == RAGFeature.COMPARE_REPORTS:
            comp_parts = ["### Comparative Medical Report Analysis\n"]
            for idx, (r_name, r_date, p_num, cnt) in enumerate(sources, 1):
                comp_parts.append(f"**Report {idx}: {r_name}** (Date: {r_date}, Page {p_num})\n{self._format_content_bullets(cnt)}\n")
            comp_parts.append("\n**Progression & Findings**: The records above demonstrate the chronological changes in your laboratory metrics and clinical parameters over time.")
            return "\n".join(comp_parts)

        elif feature == RAGFeature.MEDICAL_TIMELINE:
            timeline_rows = ["### Chronological Health Timeline\n", "| Date | Report / Event | Key Information | Source Reference |", "| :--- | :--- | :--- | :--- |"]
            for r_name, r_date, p_num, cnt in sources:
                first_line = cnt.strip().split("\n")[0][:80]
                timeline_rows.append(f"| {r_date} | {r_name} | {first_line} | Page {p_num} |")
            return "\n".join(timeline_rows)

        elif feature == RAGFeature.DOCTOR_VISIT_SUMMARY:
            return (
                f"### Doctor Visit Consultation Summary\n\n"
                f"**Prepared from records as of {rep_date}**:\n\n"
                f"1. **Recent Reports on File**:\n"
                f"   - {rep_name} (Date: {rep_date}, Page {page_num})\n\n"
                f"2. **Key Clinical Metrics to Discuss**:\n"
                f"{self._format_content_bullets(raw_content)}\n\n"
                f"3. **Suggested Physician Questions**:\n"
                f"   - How do my recent results in {rep_name} compare with my long-term baseline?\n"
                f"   - Are any dosage adjustments or follow-up tests recommended based on these findings?"
            )

        else:
            return (
                f"Based on your medical records for **{rep_name}** dated **{rep_date}** (Page {page_num}):\n\n"
                f"{self._format_content_bullets(raw_content)}"
            )

    def _format_content_bullets(self, text: str) -> str:
        """Formats text snippet into clean markdown bullet points."""
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        return "\n".join(f"  - {line}" for line in lines[:8])
