"""
Clinical Record Synthesizer for Doctor Consultation Summary Engine.
Ingests multi-source medical records and extracts structured clinical domains.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from medivault_doctor_summary.schemas.summary_schema import (
    PatientRecordInput,
    Citation,
    ConditionItem,
    AbnormalFindingItem,
    RecentReportItem,
    MedicationItem,
    FollowupItem,
)

class ClinicalRecordSynthesizer:
    """
    Synthesizes conditions, abnormal findings, medications, and follow-ups
    strictly grounded in patient source records.
    """

    KNOWN_CONDITIONS = [
        ("Type 2 Diabetes Mellitus", [r"\b(?:type\s+2\s+diabetes|t2dm|diabetes\s+mellitus\s+type\s+2|diabetes)\b"]),
        ("Essential Hypertension", [r"\b(?:essential\s+hypertension|hypertension|high\s+blood\s+pressure|htn)\b"]),
        ("Hyperlipidemia / Dyslipidemia", [r"\b(?:hyperlipidemia|dyslipidemia|high\s+cholesterol|hypercholesterolemia)\b"]),
        ("Chronic Kidney Disease", [r"\b(?:chronic\s+kidney\s+disease|ckd|renal\s+impairment|renal\s+insufficiency)\b"]),
        ("Coronary Artery Disease", [r"\b(?:coronary\s+artery\s+disease|cad|ischemic\s+heart\s+disease)\b"]),
        ("Bronchial Asthma", [r"\b(?:bronchial\s+asthma|asthma)\b"]),
        ("Hypothyroidism", [r"\b(?:hypothyroidism|underactive\s+thyroid)\b"]),
        ("Gastroesophageal Reflux Disease", [r"\b(?:gerd|acid\s+reflux|reflux\s+esophagitis)\b"]),
    ]

    LAB_THRESHOLDS = [
        {
            "pattern": r"(?:hba1c|hemoglobin\s+a1c|a1c)[\s:=]+(\d+(?:\.\d+)?)\s*(?:%)?",
            "name": "HbA1c",
            "unit": "%",
            "ref_min": 4.0,
            "ref_max": 5.6,
            "ref_str": "4.0 - 5.6%",
            "high_msg": "Elevated - sub-optimal glycemic control",
            "low_msg": "Low - potential hypoglycemia risk",
        },
        {
            "pattern": r"(?:fasting\s+(?:blood\s+)?glucose|glucose\s+fasting|fbs)[\s:=]+(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
            "name": "Fasting Blood Glucose",
            "unit": "mg/dL",
            "ref_min": 70.0,
            "ref_max": 99.0,
            "ref_str": "70 - 99 mg/dL",
            "high_msg": "Elevated fasting hyperglycemia",
            "low_msg": "Hypoglycemia",
        },
        {
            "pattern": r"(?:serum\s+creatinine|creatinine)[\s:=]+(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
            "name": "Serum Creatinine",
            "unit": "mg/dL",
            "ref_min": 0.7,
            "ref_max": 1.3,
            "ref_str": "0.7 - 1.3 mg/dL",
            "high_msg": "Elevated - decreased renal clearance",
            "low_msg": "Low serum creatinine",
        },
        {
            "pattern": r"(?:egfr|estimated\s+gfr)[\s:=]+(\d+(?:\.\d+)?)\s*(?:ml/min)?",
            "name": "eGFR",
            "unit": "mL/min/1.73m²",
            "ref_min": 90.0,
            "ref_max": 140.0,
            "ref_str": "> 90 mL/min/1.73m²",
            "high_msg": "High filtration",
            "low_msg": "Reduced filtration rate (Stage 3 CKD threshold < 60)",
        },
        {
            "pattern": r"(?:total\s+cholesterol|serum\s+cholesterol)[\s:=]+(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
            "name": "Total Cholesterol",
            "unit": "mg/dL",
            "ref_min": 125.0,
            "ref_max": 200.0,
            "ref_str": "< 200 mg/dL",
            "high_msg": "Elevated hypercholesterolemia",
            "low_msg": "Low total cholesterol",
        },
        {
            "pattern": r"(?:ldl(?:\s+cholesterol)?|ldl-c)[\s:=]+(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
            "name": "LDL Cholesterol",
            "unit": "mg/dL",
            "ref_min": 50.0,
            "ref_max": 100.0,
            "ref_str": "< 100 mg/dL",
            "high_msg": "Elevated atherogenic lipoprotein",
            "low_msg": "Optimal",
        },
        {
            "pattern": r"(?:triglycerides|tg)[\s:=]+(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
            "name": "Triglycerides",
            "unit": "mg/dL",
            "ref_min": 50.0,
            "ref_max": 150.0,
            "ref_str": "< 150 mg/dL",
            "high_msg": "Elevated hypertriglyceridemia",
            "low_msg": "Normal",
        },
    ]

    MEDICATION_PATTERNS = [
        # Example: "Metformin 500mg orally twice daily" or "Lisinopril 10 mg once daily"
        r"\b(?P<drug>metformin|lisinopril|atorvastatin|amlodipine|empagliflozin|losartan|omeprazole|levothyroxine|metoprolol|aspirin|rosuvastatin|glipizide|gabapentin)\s+(?P<dose>\d+\s*(?:mg|mcg|g)?)\s*(?P<freq>once\s+daily|twice\s+daily|daily|od|bid|tid|at\s+bedtime|qhs)?\b",
    ]

    FOLLOWUP_PATTERNS = [
        r"(?:repeat|follow[\s-]up|next\s+visit|re-check|recheck)\s+(?:in\s+)?(?P<time>\d+\s+(?:months?|weeks?|days?)|quarterly|annually)\s*(?:for\s+)?(?P<desc>[^.\n;]+)?",
        r"(?:schedule|refer\s+to|consultation\s+with)\s+(?P<spec>cardiology|endocrinology|nephrology|ophthalmology|podiatry|pulmonology)\s*(?:in\s+)?(?P<time2>\d+\s+(?:months?|weeks?))?",
    ]

    def synthesize_all_records(
        self,
        records: List[PatientRecordInput],
    ) -> Tuple[
        List[ConditionItem],
        List[AbnormalFindingItem],
        List[RecentReportItem],
        List[MedicationItem],
        List[FollowupItem],
    ]:
        conditions = self._extract_conditions(records)
        abnormals = self._extract_abnormal_findings(records)
        recent_reports = self._extract_recent_reports(records)
        medications = self._extract_medications(records)
        followups = self._extract_followups(records)

        return conditions, abnormals, recent_reports, medications, followups

    def _extract_conditions(self, records: List[PatientRecordInput]) -> List[ConditionItem]:
        conditions: List[ConditionItem] = []
        seen = set()

        for rec in records:
            content_lower = rec.content.lower()
            cite = Citation(
                report_name=rec.report_name,
                page_number=rec.page_number,
                report_date=rec.report_date,
                document_id=rec.document_id,
            )

            for canonical_name, patterns in self.KNOWN_CONDITIONS:
                if canonical_name in seen:
                    continue
                for pat in patterns:
                    if re.search(pat, content_lower, re.IGNORECASE):
                        conditions.append(
                            ConditionItem(
                                name=canonical_name,
                                status="ACTIVE",
                                diagnosed_date=rec.report_date,
                                citation=cite,
                            )
                        )
                        seen.add(canonical_name)
                        break

        return conditions

    def _extract_abnormal_findings(self, records: List[PatientRecordInput]) -> List[AbnormalFindingItem]:
        abnormals: List[AbnormalFindingItem] = []
        seen = set()

        for rec in records:
            cite = Citation(
                report_name=rec.report_name,
                page_number=rec.page_number,
                report_date=rec.report_date,
                document_id=rec.document_id,
            )

            # Blood pressure check
            bp_match = re.search(r"(?:blood\s+pressure|bp)[\s:=]+(\d{2,3})/(\d{2,3})", rec.content, re.IGNORECASE)
            if bp_match:
                sys = float(bp_match.group(1))
                dia = float(bp_match.group(2))
                key = (rec.report_date, "Blood Pressure")
                if key not in seen and (sys >= 130.0 or dia >= 85.0):
                    interp = "Stage 2 Hypertension" if (sys >= 140.0 or dia >= 90.0) else "Elevated Blood Pressure"
                    abnormals.append(
                        AbnormalFindingItem(
                            test_name="Blood Pressure",
                            value=sys,
                            unit=f"/{int(dia)} mmHg",
                            reference_range="< 120/80 mmHg",
                            clinical_interpretation=interp,
                            citation=cite,
                        )
                    )
                    seen.add(key)

            for cfg in self.LAB_THRESHOLDS:
                for match in re.finditer(cfg["pattern"], rec.content, re.IGNORECASE):
                    val = float(match.group(1))
                    key = (rec.report_date, cfg["name"])
                    if key in seen:
                        continue

                    # Check if abnormal
                    if val > cfg["ref_max"]:
                        abnormals.append(
                            AbnormalFindingItem(
                                test_name=cfg["name"],
                                value=val,
                                unit=cfg["unit"],
                                reference_range=cfg["ref_str"],
                                clinical_interpretation=cfg["high_msg"],
                                citation=cite,
                            )
                        )
                        seen.add(key)
                    elif val < cfg["ref_min"]:
                        abnormals.append(
                            AbnormalFindingItem(
                                test_name=cfg["name"],
                                value=val,
                                unit=cfg["unit"],
                                reference_range=cfg["ref_str"],
                                clinical_interpretation=cfg["low_msg"],
                                citation=cite,
                            )
                        )
                        seen.add(key)

        return abnormals

    def _extract_recent_reports(self, records: List[PatientRecordInput]) -> List[RecentReportItem]:
        # Sort chronologically (newest first)
        sorted_recs = sorted(records, key=lambda x: x.report_date, reverse=True)
        recent: List[RecentReportItem] = []

        for rec in sorted_recs:
            # Extract high-level impression or first sentence
            sentences = [s.strip() for s in re.split(r"[.\n]", rec.content) if len(s.strip()) > 10]
            impression = sentences[0] if sentences else f"{rec.category} document reviewed."
            if len(impression) > 120:
                impression = impression[:117] + "..."

            cite = Citation(
                report_name=rec.report_name,
                page_number=rec.page_number,
                report_date=rec.report_date,
                document_id=rec.document_id,
            )

            recent.append(
                RecentReportItem(
                    report_name=rec.report_name,
                    report_date=rec.report_date,
                    category=rec.category,
                    key_impression=impression,
                    citation=cite,
                )
            )

        return recent

    def _extract_medications(self, records: List[PatientRecordInput]) -> List[MedicationItem]:
        meds: List[MedicationItem] = []
        seen = set()

        for rec in records:
            cite = Citation(
                report_name=rec.report_name,
                page_number=rec.page_number,
                report_date=rec.report_date,
                document_id=rec.document_id,
            )

            for pat in self.MEDICATION_PATTERNS:
                for match in re.finditer(pat, rec.content, re.IGNORECASE):
                    gd = match.groupdict()
                    drug = gd.get("drug", "").capitalize()
                    dose = gd.get("dose", "As directed")
                    freq = gd.get("freq") or "Daily"

                    if drug in seen:
                        continue

                    # Associate indication if obvious
                    indication = None
                    if drug.lower() in ("metformin", "empagliflozin", "glipizide"):
                        indication = "Type 2 Diabetes Mellitus"
                    elif drug.lower() in ("lisinopril", "losartan", "amlodipine", "metoprolol"):
                        indication = "Hypertension"
                    elif drug.lower() in ("atorvastatin", "rosuvastatin"):
                        indication = "Hyperlipidemia"
                    elif drug.lower() in ("omeprazole",):
                        indication = "GERD"

                    meds.append(
                        MedicationItem(
                            drug_name=drug,
                            dosage=dose,
                            frequency=freq,
                            indication=indication,
                            prescribing_doctor=rec.doctor_name,
                            citation=cite,
                        )
                    )
                    seen.add(drug)

        return meds

    def _extract_followups(self, records: List[PatientRecordInput]) -> List[FollowupItem]:
        followups: List[FollowupItem] = []
        seen = set()

        for rec in records:
            cite = Citation(
                report_name=rec.report_name,
                page_number=rec.page_number,
                report_date=rec.report_date,
                document_id=rec.document_id,
            )

            for pat in self.FOLLOWUP_PATTERNS:
                for match in re.finditer(pat, rec.content, re.IGNORECASE):
                    gd = match.groupdict()
                    timeframe = gd.get("time") or gd.get("time2") or "Upcoming cycle"
                    spec = gd.get("spec") or gd.get("desc") or "Follow-up consultation"
                    spec = spec.strip().capitalize()

                    key = (spec, timeframe)
                    if key in seen:
                        continue

                    followups.append(
                        FollowupItem(
                            specialty_or_test=spec,
                            target_timeframe=timeframe,
                            instructions=f"Recommended monitoring interval: {timeframe} for {spec}.",
                            citation=cite,
                        )
                    )
                    seen.add(key)

        return followups

    def generate_discussion_questions(
        self,
        conditions: List[ConditionItem],
        abnormals: List[AbnormalFindingItem],
        medications: List[MedicationItem],
        followups: List[FollowupItem],
    ) -> List[str]:
        """
        Generates high-yield, personalized questions for the patient to ask their physician.
        """
        questions: List[str] = []

        # 1. Questions on abnormal lab values
        for ab in abnormals:
            if ab.test_name == "HbA1c":
                questions.append(
                    f"My latest HbA1c is {ab.value}% (above normal reference range {ab.reference_range}). "
                    "Should we consider modifying my medication dosages or lifestyle plan to achieve tighter glycemic control?"
                )
            elif ab.test_name == "Blood Pressure":
                questions.append(
                    f"My blood pressure was recorded elevated at {ab.value}{ab.unit}. "
                    "Do we need to adjust my antihypertensive regimen or start home blood pressure log tracking?"
                )
            elif ab.test_name in ("eGFR", "Serum Creatinine"):
                questions.append(
                    f"My kidney markers show {ab.test_name} at {ab.value} {ab.unit} ({ab.clinical_interpretation}). "
                    "Are there any medication adjustments or renal precautions I should observe?"
                )
            elif ab.test_name in ("LDL Cholesterol", "Total Cholesterol"):
                questions.append(
                    f"My lipid profile indicates elevated {ab.test_name} of {ab.value} {ab.unit}. "
                    "Is my current statin therapy sufficient, or do we need to optimize the dosage?"
                )

        # 2. Medication interaction / side effects question
        if medications:
            med_names = ", ".join([m.drug_name for m in medications[:3]])
            questions.append(
                f"Are there any drug interactions or monitoring requirements between my current prescriptions ({med_names})?"
            )

        # 3. Followup / preventative milestones
        if followups:
            f = followups[0]
            questions.append(
                f"For my upcoming {f.specialty_or_test} ({f.target_timeframe}), what preliminary diagnostic tests should be completed beforehand?"
            )
        else:
            questions.append(
                "What is our target timeline for re-evaluating my routine laboratory panels?"
            )

        # Ensure at least 3 concise questions
        if len(questions) < 3:
            questions.append("What specific symptoms or warning signs should prompt me to contact the clinic sooner?")

        return questions[:5]
