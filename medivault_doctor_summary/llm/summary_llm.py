"""
Doctor Summary LLM Engine and Markdown Formatter.
Constructs the exact requested clinical briefing note format with grounded citations.
"""
from typing import List, Dict, Any, Optional
from medivault_doctor_summary.schemas.summary_schema import (
    ConditionItem,
    AbnormalFindingItem,
    RecentReportItem,
    MedicationItem,
    FollowupItem,
    Citation,
)

class DoctorSummaryLLMEngine:
    """
    Renders the exact formatted clinical consultation summary adhering to:
    - Patient Summary
    - Abnormal Findings
    - Recent Reports
    - Current Medications
    - Upcoming Followups
    - Questions To Discuss With Physician
    """

    def generate_patient_overview(
        self,
        patient_id: str,
        patient_name: Optional[str],
        conditions: List[ConditionItem],
        abnormals: List[AbnormalFindingItem],
        medications: List[MedicationItem],
        recent_reports: List[RecentReportItem],
    ) -> str:
        """
        Generates a concise, high-yield clinical overview paragraph.
        """
        p_name = patient_name or f"Patient {patient_id}"
        cond_str = ", ".join([c.name for c in conditions]) if conditions else "general wellness monitoring"
        
        dates = sorted({r.report_date for r in recent_reports if r.report_date})
        interval_str = f"{dates[0]} to {dates[-1]}" if len(dates) >= 2 else (dates[0] if dates else "recent clinical review")

        abnormal_summary = ""
        if abnormals:
            abnormal_names = [f"{a.test_name} ({a.value} {a.unit})" for a in abnormals[:3]]
            abnormal_summary = f" Out-of-range biomarkers requiring physician review include {', '.join(abnormal_names)}."
        else:
            abnormal_summary = " All reviewed laboratory parameters remain within standard reference thresholds."

        med_summary = ""
        if medications:
            med_summary = f" The patient is currently maintained on {len(medications)} active prescription(s) including {', '.join([m.drug_name for m in medications[:3]])}."

        overview = (
            f"Clinical consultation brief for {p_name} covering medical records from {interval_str}. "
            f"Active clinical management focuses on {cond_str}.{abnormal_summary}{med_summary} "
            "This briefing note is synthesized directly from verified patient records for review with the attending physician."
        )
        return overview

    def render_markdown(
        self,
        patient_summary: str,
        conditions: List[ConditionItem],
        abnormals: List[AbnormalFindingItem],
        recent_reports: List[RecentReportItem],
        medications: List[MedicationItem],
        followups: List[FollowupItem],
        questions: List[str],
    ) -> str:
        """
        Builds the exact required markdown format:
        Patient Summary
        ...
        Abnormal Findings
        ...
        Recent Reports
        ...
        Current Medications
        ...
        Questions To Discuss With Physician
        ...
        """
        sections: List[str] = []

        # Section 1: Patient Summary
        sections.append("Patient Summary\n")
        sections.append(patient_summary.strip() + "\n")

        # Active Conditions (Clinical context)
        if conditions:
            sections.append("\nCurrent Conditions")
            for c in conditions:
                sections.append(f"- **{c.name}** ({c.status}) [Source: {c.citation.report_name}, Page {c.citation.page_number}, {c.citation.report_date}]")
            sections.append("")

        # Section 2: Abnormal Findings
        sections.append("\nAbnormal Findings")
        if abnormals:
            for ab in abnormals:
                sections.append(
                    f"- **{ab.test_name}**: {ab.value} {ab.unit} (Ref: {ab.reference_range}) - {ab.clinical_interpretation} "
                    f"[Source: {ab.citation.report_name}, Page {ab.citation.page_number}, {ab.citation.report_date}]"
                )
        else:
            sections.append("- No abnormal lab values documented in reviewed records.")
        sections.append("")

        # Section 3: Recent Reports
        sections.append("\nRecent Reports")
        if recent_reports:
            for rep in recent_reports:
                sections.append(
                    f"- **{rep.report_date}** - {rep.report_name} ({rep.category}): {rep.key_impression} "
                    f"[Source: {rep.citation.report_name}, Page {rep.citation.page_number}, {rep.citation.report_date}]"
                )
        else:
            sections.append("- No recent clinical reports available.")
        sections.append("")

        # Section 4: Current Medications
        sections.append("\nCurrent Medications")
        if medications:
            for m in medications:
                ind_str = f" (for {m.indication})" if m.indication else ""
                dr_str = f" prescribed by Dr. {m.prescribing_doctor}" if m.prescribing_doctor else ""
                sections.append(
                    f"- **{m.drug_name}** {m.dosage} {m.frequency}{ind_str}{dr_str} "
                    f"[Source: {m.citation.report_name}, Page {m.citation.page_number}, {m.citation.report_date}]"
                )
        else:
            sections.append("- No active prescription medications documented in reviewed records.")
        sections.append("")

        # Upcoming Followups
        if followups:
            sections.append("\nUpcoming Followups")
            for f in followups:
                sections.append(
                    f"- **{f.specialty_or_test}**: {f.instructions} ({f.target_timeframe}) "
                    f"[Source: {f.citation.report_name}, Page {f.citation.page_number}, {f.citation.report_date}]"
                )
            sections.append("")

        # Section 5: Questions To Discuss With Physician
        sections.append("\nQuestions To Discuss With Physician")
        if questions:
            for i, q in enumerate(questions, start=1):
                sections.append(f"{i}. {q}")
        else:
            sections.append("1. What preventative milestones or routine screening panels are recommended at this stage?")

        return "\n".join(sections).strip()
