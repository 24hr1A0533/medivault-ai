"""
Clinical Biomarker Catalog for Medical Trend Analysis.
Defines canonical reference ranges, clinical directionality, and alert triggers.
"""
from typing import Dict, Any, Optional
from enum import Enum

class DesiredDirection(str, Enum):
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    WITHIN_RANGE_IS_BETTER = "WITHIN_RANGE_IS_BETTER"

class BiomarkerProfile:
    def __init__(
        self,
        canonical_name: str,
        aliases: list[str],
        default_unit: str,
        normal_min: float,
        normal_max: float,
        desired_direction: DesiredDirection,
        significant_delta_pct: float,
        critical_high: Optional[float] = None,
        critical_low: Optional[float] = None,
        clinical_description: str = "",
    ):
        self.canonical_name = canonical_name
        self.aliases = [a.lower() for a in aliases]
        self.default_unit = default_unit
        self.normal_min = normal_min
        self.normal_max = normal_max
        self.desired_direction = desired_direction
        self.significant_delta_pct = significant_delta_pct
        self.critical_high = critical_high
        self.critical_low = critical_low
        self.clinical_description = clinical_description

CATALOG: Dict[str, BiomarkerProfile] = {
    "HbA1c": BiomarkerProfile(
        canonical_name="HbA1c",
        aliases=["hba1c", "glycated hemoglobin", "a1c", "hemoglobin a1c", "glycosylated hemoglobin"],
        default_unit="%",
        normal_min=4.0,
        normal_max=5.6,
        desired_direction=DesiredDirection.LOWER_IS_BETTER,
        significant_delta_pct=5.0,
        critical_high=9.0,
        clinical_description="Average blood glucose level over past 2-3 months. Target for non-diabetics is < 5.7%, diabetic control goal is < 7.0%.",
    ),
    "Fasting Blood Glucose": BiomarkerProfile(
        canonical_name="Fasting Blood Glucose",
        aliases=["fasting blood glucose", "fasting glucose", "fbs", "glucose fasting", "blood sugar fasting"],
        default_unit="mg/dL",
        normal_min=70.0,
        normal_max=99.0,
        desired_direction=DesiredDirection.LOWER_IS_BETTER,
        significant_delta_pct=10.0,
        critical_high=200.0,
        critical_low=54.0,
        clinical_description="Plasma glucose measured after an 8-hour fast. Normal < 100 mg/dL.",
    ),
    "Serum Creatinine": BiomarkerProfile(
        canonical_name="Serum Creatinine",
        aliases=["serum creatinine", "creatinine", "creat"],
        default_unit="mg/dL",
        normal_min=0.7,
        normal_max=1.3,
        desired_direction=DesiredDirection.LOWER_IS_BETTER,
        significant_delta_pct=15.0,
        critical_high=2.5,
        clinical_description="Byproduct of muscle metabolism filtered by kidneys. Elevated levels suggest impaired renal clearance.",
    ),
    "eGFR": BiomarkerProfile(
        canonical_name="eGFR",
        aliases=["egfr", "estimated glomerular filtration rate", "gfr"],
        default_unit="mL/min/1.73m²",
        normal_min=90.0,
        normal_max=130.0,
        desired_direction=DesiredDirection.HIGHER_IS_BETTER,
        significant_delta_pct=10.0,
        critical_low=30.0,
        clinical_description="Key metric of kidney function. Values < 60 mL/min/1.73m² indicate chronic kidney disease.",
    ),
    "Total Cholesterol": BiomarkerProfile(
        canonical_name="Total Cholesterol",
        aliases=["total cholesterol", "cholesterol total", "serum cholesterol"],
        default_unit="mg/dL",
        normal_min=125.0,
        normal_max=200.0,
        desired_direction=DesiredDirection.LOWER_IS_BETTER,
        significant_delta_pct=8.0,
        critical_high=260.0,
        clinical_description="Total amount of cholesterol in blood. Desirable level is < 200 mg/dL.",
    ),
    "LDL Cholesterol": BiomarkerProfile(
        canonical_name="LDL Cholesterol",
        aliases=["ldl cholesterol", "ldl", "low density lipoprotein", "ldl-c"],
        default_unit="mg/dL",
        normal_min=50.0,
        normal_max=100.0,
        desired_direction=DesiredDirection.LOWER_IS_BETTER,
        significant_delta_pct=10.0,
        critical_high=190.0,
        clinical_description="Low-density lipoprotein. Primary atherogenic particle; optimal level is < 100 mg/dL.",
    ),
    "HDL Cholesterol": BiomarkerProfile(
        canonical_name="HDL Cholesterol",
        aliases=["hdl cholesterol", "hdl", "high density lipoprotein", "hdl-c"],
        default_unit="mg/dL",
        normal_min=40.0,
        normal_max=60.0,
        desired_direction=DesiredDirection.HIGHER_IS_BETTER,
        significant_delta_pct=10.0,
        critical_low=30.0,
        clinical_description="High-density lipoprotein. Cardioprotective biomarker; higher values (> 50 mg/dL) are favorable.",
    ),
    "Triglycerides": BiomarkerProfile(
        canonical_name="Triglycerides",
        aliases=["triglycerides", "tg", "trig"],
        default_unit="mg/dL",
        normal_min=50.0,
        normal_max=150.0,
        desired_direction=DesiredDirection.LOWER_IS_BETTER,
        significant_delta_pct=15.0,
        critical_high=400.0,
        clinical_description="Type of fat in the blood. Normal is < 150 mg/dL; > 500 mg/dL increases pancreatitis risk.",
    ),
    "Systolic Blood Pressure": BiomarkerProfile(
        canonical_name="Systolic Blood Pressure",
        aliases=["systolic bp", "systolic blood pressure", "sbp", "systolic"],
        default_unit="mmHg",
        normal_min=90.0,
        normal_max=120.0,
        desired_direction=DesiredDirection.WITHIN_RANGE_IS_BETTER,
        significant_delta_pct=8.0,
        critical_high=180.0,
        critical_low=80.0,
        clinical_description="Pressure in arteries when heart beats. Normal < 120 mmHg; Stage 2 hypertension >= 140 mmHg.",
    ),
    "Diastolic Blood Pressure": BiomarkerProfile(
        canonical_name="Diastolic Blood Pressure",
        aliases=["diastolic bp", "diastolic blood pressure", "dbp", "diastolic"],
        default_unit="mmHg",
        normal_min=60.0,
        normal_max=80.0,
        desired_direction=DesiredDirection.WITHIN_RANGE_IS_BETTER,
        significant_delta_pct=8.0,
        critical_high=120.0,
        critical_low=50.0,
        clinical_description="Pressure in arteries between heart beats. Normal < 80 mmHg; Stage 2 hypertension >= 90 mmHg.",
    ),
    "Hemoglobin": BiomarkerProfile(
        canonical_name="Hemoglobin",
        aliases=["hemoglobin", "hgb", "hb"],
        default_unit="g/dL",
        normal_min=12.0,
        normal_max=17.0,
        desired_direction=DesiredDirection.WITHIN_RANGE_IS_BETTER,
        significant_delta_pct=10.0,
        critical_low=7.0,
        critical_high=20.0,
        clinical_description="Oxygen-carrying protein in red blood cells. Low values indicate anemia.",
    ),
}

def resolve_biomarker(name: str) -> Optional[BiomarkerProfile]:
    """
    Resolves any clinical test name or alias to its canonical BiomarkerProfile.
    """
    clean = name.strip().lower()
    for profile in CATALOG.values():
        if clean == profile.canonical_name.lower() or clean in profile.aliases:
            return profile
    return None
