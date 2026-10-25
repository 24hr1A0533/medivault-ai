"""
Report Parser for Medical Trend Analysis Engine.
Extracts actual clinical measurements from raw patient reports without interpolation.
"""
import re
from typing import List, Dict, Any, Optional
from medivault_trend_engine.schemas.trend_schema import BiomarkerMeasurement
from medivault_trend_engine.biomarkers.biomarker_catalog import resolve_biomarker, CATALOG

class ClinicalReportParser:
    """
    Extracts biomarker measurements strictly from authentic report text or structured records.
    Never invents or hallucinates missing numbers.
    """

    PATTERNS = [
        # Example: "HbA1c: 8.5 %" or "HbA1c = 7.1%" or "HbA1c 6.3%"
        r"(?P<name>hba1c|glycated\s+hemoglobin|hemoglobin\s+a1c|a1c)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>%|percent)?",
        # Example: "Fasting Blood Glucose: 142 mg/dL" or "Glucose Fasting 98 mg/dl"
        r"(?P<name>fasting\s+(?:blood\s+)?glucose|glucose\s+fasting|fbs)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg/dl|mmol/l)?",
        # Example: "Serum Creatinine: 1.2 mg/dL"
        r"(?P<name>serum\s+creatinine|creatinine)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg/dl|umol/l)?",
        # Example: "eGFR: 88 mL/min/1.73m2"
        r"(?P<name>egfr|estimated\s+gfr)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>ml/min(?:/1\.73m2)?)?",
        # Example: "Total Cholesterol: 210 mg/dL"
        r"(?P<name>total\s+cholesterol|serum\s+cholesterol)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg/dl|mmol/l)?",
        # Example: "LDL Cholesterol: 130 mg/dL"
        r"(?P<name>ldl\s+(?:cholesterol)?|ldl-c)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg/dl|mmol/l)?",
        # Example: "HDL Cholesterol: 45 mg/dL"
        r"(?P<name>hdl\s+(?:cholesterol)?|hdl-c)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg/dl|mmol/l)?",
        # Example: "Triglycerides: 180 mg/dL"
        r"(?P<name>triglycerides|tg)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg/dl|mmol/l)?",
        # Example: "Blood Pressure: 138/88 mmHg"
        r"(?P<name>blood\s+pressure|bp)[\s:=]+(?P<sys>\d{2,3})/(?P<dia>\d{2,3})\s*(?P<unit>mmhg)?",
        # Example: "Hemoglobin: 14.2 g/dL"
        r"(?P<name>hemoglobin|hgb|hb)[\s:=]+(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>g/dl)?",
    ]

    def __init__(self):
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.PATTERNS]

    def parse_report_text(
        self,
        text: str,
        report_name: str,
        report_date: str,
        page_number: int = 1,
        document_id: Optional[str] = None,
    ) -> List[BiomarkerMeasurement]:
        """
        Extracts biomarkers from unformatted clinical report text.
        """
        measurements: List[BiomarkerMeasurement] = []
        seen_canonical = set()

        # Blood pressure special dual-value regex match
        bp_match = re.search(r"(?:blood\s+pressure|bp)[\s:=]+(\d{2,3})/(\d{2,3})\s*(?:mmhg)?", text, re.IGNORECASE)
        if bp_match:
            sys_val = float(bp_match.group(1))
            dia_val = float(bp_match.group(2))
            measurements.append(
                BiomarkerMeasurement(
                    test_name="Systolic Blood Pressure",
                    value=sys_val,
                    unit="mmHg",
                    reference_range="90 - 120",
                    report_name=report_name,
                    page_number=page_number,
                    report_date=report_date,
                    document_id=document_id,
                )
            )
            measurements.append(
                BiomarkerMeasurement(
                    test_name="Diastolic Blood Pressure",
                    value=dia_val,
                    unit="mmHg",
                    reference_range="60 - 80",
                    report_name=report_name,
                    page_number=page_number,
                    report_date=report_date,
                    document_id=document_id,
                )
            )
            seen_canonical.add("Systolic Blood Pressure")
            seen_canonical.add("Diastolic Blood Pressure")

        for regex in self._compiled:
            for match in regex.finditer(text):
                gd = match.groupdict()
                if "val" not in gd or not gd["val"]:
                    continue

                raw_name = gd.get("name", "")
                profile = resolve_biomarker(raw_name)
                if not profile or profile.canonical_name in seen_canonical:
                    continue

                val = float(gd["val"])
                unit = gd.get("unit") or profile.default_unit

                measurements.append(
                    BiomarkerMeasurement(
                        test_name=profile.canonical_name,
                        value=val,
                        unit=unit,
                        reference_range=f"{profile.normal_min} - {profile.normal_max}",
                        report_name=report_name,
                        page_number=page_number,
                        report_date=report_date,
                        document_id=document_id,
                    )
                )
                seen_canonical.add(profile.canonical_name)

        return measurements
