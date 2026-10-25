"""
Pydantic Schemas for MediVault Medical Trend Analysis Engine.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class TrendDirection(str, Enum):
    IMPROVING = "IMPROVING"
    DETERIORATING = "DETERIORATING"
    STABLE = "STABLE"
    FLUCTUATING = "FLUCTUATING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class AlertSeverity(str, Enum):
    NONE = "NONE"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class ReportCitation(BaseModel):
    report_name: str = Field(..., description="Name of the clinical document")
    page_number: int = Field(..., description="1-indexed page number")
    report_date: str = Field(..., description="Date of the report YYYY-MM-DD")
    document_id: Optional[str] = None

class BiomarkerMeasurement(BaseModel):
    test_name: str = Field(..., description="Canonical test name (e.g., HbA1c, Fasting Glucose)")
    value: float = Field(..., description="Measured numerical biomarker value")
    unit: str = Field(..., description="Unit of measurement (e.g. %, mg/dL)")
    reference_range: Optional[str] = Field(default=None, description="Standard lab normal range")
    report_name: str
    page_number: int
    report_date: str
    document_id: Optional[str] = None

class ImprovementSummary(BaseModel):
    biomarker_name: str
    baseline_date: str
    baseline_value: float
    latest_date: str
    latest_value: float
    unit: str
    delta_absolute: float
    delta_percent: float
    clinical_significance: str
    citations: List[ReportCitation]

class DeteriorationAlert(BaseModel):
    biomarker_name: str
    severity: AlertSeverity
    alert_message: str
    baseline_date: str
    baseline_value: float
    latest_date: str
    latest_value: float
    unit: str
    delta_absolute: float
    delta_percent: float
    clinical_risk: str
    citations: List[ReportCitation]

class TrendGraphData(BaseModel):
    biomarker_name: str
    unit: str
    dates: List[str]
    values: List[float]
    normal_min: Optional[float] = None
    normal_max: Optional[float] = None
    svg_render: str = Field(..., description="Inline clean SVG representation of the trend line")
    json_points: List[Dict[str, Any]] = Field(..., description="Structured points for frontend charting (Chart.js / Recharts)")
    citations: List[ReportCitation]

class MarkerTrendResult(BaseModel):
    biomarker_name: str
    data_points: List[BiomarkerMeasurement]
    direction: TrendDirection
    delta_absolute: float
    delta_percent: float
    is_currently_normal: bool
    improvement_summary: Optional[ImprovementSummary] = None
    deterioration_alert: Optional[DeteriorationAlert] = None
    graph: Optional[TrendGraphData] = None
    citations: List[ReportCitation]

class DoctorReadySummary(BaseModel):
    headline: str
    patient_id: str
    monitoring_interval: str
    biomarkers_reviewed: List[str]
    clinical_trajectory: str
    priority_action_items: List[str]
    citations: List[ReportCitation]

class PatientTrendAnalysisRequest(BaseModel):
    patient_id: str = Field(..., min_length=1)
    raw_reports: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional raw reports to parse")
    preparsed_measurements: Optional[List[BiomarkerMeasurement]] = Field(default=None)
    target_biomarkers: Optional[List[str]] = Field(default=None)

class PatientTrendAnalysisResponse(BaseModel):
    patient_id: str
    summary: str
    explanation: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    marker_trends: Dict[str, MarkerTrendResult]
    trend_graphs: List[TrendGraphData]
    improvement_summaries: List[ImprovementSummary]
    deterioration_alerts: List[DeteriorationAlert]
    doctor_ready_summary: DoctorReadySummary
    citations: List[ReportCitation]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
