"""
Test suite for MediVault Medical Trend Analysis Engine.

Verifies:
- User HbA1c progression example: Jan = 8.5%, Apr = 7.1%, Jul = 6.3%
- Trend graphs generation (SVG + JSON points)
- Improvement summaries with source citations
- Deterioration alerts with severity and clinical risk
- Doctor-ready summary generation
- Non-invention guarantee: never hallucinates missing numbers
- REST API integration via TestClient
"""
import pytest
from fastapi.testclient import TestClient

from medivault_trend_engine.schemas.trend_schema import (
    BiomarkerMeasurement,
    TrendDirection,
    AlertSeverity,
    PatientTrendAnalysisRequest,
)
from medivault_trend_engine.engine.trend_analyzer import ClinicalTrendAnalyzer
from medivault_trend_engine.extractor.report_parser import ClinicalReportParser
from medivault_trend_engine.visualizer.graph_generator import TrendGraphGenerator
from medivault_trend_engine.main import app

@pytest.fixture
def analyzer():
    return ClinicalTrendAnalyzer()

@pytest.fixture
def parser():
    return ClinicalReportParser()

@pytest.fixture
def client():
    return TestClient(app)


def test_hba1c_user_example_trend_improvement(analyzer):
    """
    Test exact user scenario:
    HbA1c:
    Jan = 8.5
    Apr = 7.1
    Jul = 6.3

    Must generate:
    - trend direction: IMPROVING
    - trend graphs with SVG render
    - improvement summaries
    - doctor-ready summary
    - citations for Jan, Apr, Jul reports
    - confidence score >= 0.95
    """
    measurements = [
        BiomarkerMeasurement(
            test_name="HbA1c",
            value=8.5,
            unit="%",
            reference_range="4.0 - 5.6",
            report_name="Comprehensive Lab Panel - Jan 2026",
            page_number=1,
            report_date="2026-01-15",
            document_id="DOC-JAN-001",
        ),
        BiomarkerMeasurement(
            test_name="HbA1c",
            value=7.1,
            unit="%",
            reference_range="4.0 - 5.6",
            report_name="Quarterly Glycemic Review - Apr 2026",
            page_number=2,
            report_date="2026-04-12",
            document_id="DOC-APR-002",
        ),
        BiomarkerMeasurement(
            test_name="HbA1c",
            value=6.3,
            unit="%",
            reference_range="4.0 - 5.6",
            report_name="Endocrinology Progress Report - Jul 2026",
            page_number=1,
            report_date="2026-07-20",
            document_id="DOC-JUL-003",
        ),
    ]

    response = analyzer.analyze_patient_trends(
        patient_id="PATIENT-1001",
        measurements=measurements,
    )

    assert response.patient_id == "PATIENT-1001"
    assert "HbA1c" in response.marker_trends
    hba1c_trend = response.marker_trends["HbA1c"]

    # 1. Trend Direction & Deltas
    assert hba1c_trend.direction == TrendDirection.IMPROVING
    assert hba1c_trend.delta_absolute == -2.2
    assert hba1c_trend.delta_percent == -25.88

    # 2. Improvement Summary
    assert len(response.improvement_summaries) == 1
    imp = response.improvement_summaries[0]
    assert imp.biomarker_name == "HbA1c"
    assert imp.baseline_value == 8.5
    assert imp.latest_value == 6.3
    assert imp.baseline_date == "2026-01-15"
    assert imp.latest_date == "2026-07-20"
    assert "improved by 2.2" in imp.clinical_significance or "improved" in imp.clinical_significance

    # 3. No False Deterioration Alerts
    assert len(response.deterioration_alerts) == 0

    # 4. Trend Graph (SVG + JSON points)
    assert len(response.trend_graphs) == 1
    graph = response.trend_graphs[0]
    assert graph.biomarker_name == "HbA1c"
    assert "<svg" in graph.svg_render
    assert "</svg>" in graph.svg_render
    assert "8.5" in graph.svg_render
    assert "6.3" in graph.svg_render
    assert len(graph.json_points) == 3
    assert graph.json_points[0]["value"] == 8.5
    assert graph.json_points[2]["value"] == 6.3

    # 5. Doctor-Ready Summary
    doc = response.doctor_ready_summary
    assert "PATIENT-1001" in doc.patient_id
    assert "2026-01-15 to 2026-07-20" in doc.monitoring_interval
    assert len(doc.priority_action_items) > 0
    assert any("Reinforce favorable progress" in act for act in doc.priority_action_items)

    # 6. Citations
    assert len(response.citations) == 3
    report_names = {c.report_name for c in response.citations}
    assert "Comprehensive Lab Panel - Jan 2026" in report_names
    assert "Quarterly Glycemic Review - Apr 2026" in report_names
    assert "Endocrinology Progress Report - Jul 2026" in report_names

    # 7. Confidence Score (3 points with verified metadata -> high confidence)
    assert response.confidence_score >= 0.95


def test_deterioration_alert_generation(analyzer):
    """
    Test deterioration detection:
    Renal eGFR drops from 95 mL/min/1.73m² (Jan) to 52 mL/min/1.73m² (Jun).
    Must trigger DeteriorationAlert.
    """
    measurements = [
        BiomarkerMeasurement(
            test_name="eGFR",
            value=95.0,
            unit="mL/min/1.73m²",
            reference_range="> 90",
            report_name="Renal Baseline - Jan",
            page_number=1,
            report_date="2026-01-10",
        ),
        BiomarkerMeasurement(
            test_name="eGFR",
            value=52.0,
            unit="mL/min/1.73m²",
            reference_range="> 90",
            report_name="Renal Followup - Jun",
            page_number=1,
            report_date="2026-06-18",
        ),
    ]

    response = analyzer.analyze_patient_trends(
        patient_id="PATIENT-2002",
        measurements=measurements,
    )

    assert "eGFR" in response.marker_trends
    trend = response.marker_trends["eGFR"]
    assert trend.direction == TrendDirection.DETERIORATING
    assert trend.delta_absolute == -43.0

    assert len(response.deterioration_alerts) == 1
    alert = response.deterioration_alerts[0]
    assert alert.biomarker_name == "eGFR"
    assert alert.severity in (AlertSeverity.WARNING, AlertSeverity.CRITICAL)
    assert "Deterioration Alert" in alert.alert_message
    assert len(alert.citations) == 2


def test_never_invent_values_on_unrecorded_tests(analyzer):
    """
    Verify non-invention requirement:
    If report contains only Fasting Blood Glucose, system NEVER creates or hallucinates
    HbA1c or Cholesterol.
    """
    measurements = [
        BiomarkerMeasurement(
            test_name="Fasting Blood Glucose",
            value=105.0,
            unit="mg/dL",
            reference_range="70 - 99",
            report_name="Metabolic Lab",
            page_number=1,
            report_date="2026-02-01",
        ),
        BiomarkerMeasurement(
            test_name="Fasting Blood Glucose",
            value=96.0,
            unit="mg/dL",
            reference_range="70 - 99",
            report_name="Metabolic Lab 2",
            page_number=1,
            report_date="2026-05-01",
        ),
    ]

    response = analyzer.analyze_patient_trends(
        patient_id="PATIENT-3003",
        measurements=measurements,
    )

    # Only Fasting Blood Glucose is present
    assert list(response.marker_trends.keys()) == ["Fasting Blood Glucose"]
    assert "HbA1c" not in response.marker_trends
    assert "Total Cholesterol" not in response.marker_trends
    assert "Serum Creatinine" not in response.marker_trends


def test_empty_records_returns_fallback_message(analyzer):
    """
    If no records exist, return the exact negative requirement fallback.
    """
    response = analyzer.analyze_patient_trends(
        patient_id="PATIENT-EMPTY",
        measurements=[],
    )
    assert response.confidence_score == 0.0
    assert response.explanation == "I could not find that information in your medical records."
    assert len(response.citations) == 0


def test_report_parser_extraction(parser):
    """
    Test automatic regex and clinical extraction from doctor visit notes and lab text.
    """
    sample_text = """
    PATIENT EVALUATION RECORD
    Vital Signs: Blood Pressure: 132/84 mmHg
    Laboratory Findings:
    HbA1c: 7.4 % (Reference: 4.0 - 5.6%)
    Fasting Blood Glucose: 138 mg/dL
    Serum Creatinine: 1.1 mg/dL
    eGFR: 78 mL/min/1.73m2
    Total Cholesterol: 218 mg/dL
    """

    measurements = parser.parse_report_text(
        text=sample_text,
        report_name="Spring Clinical Note",
        report_date="2026-03-15",
        page_number=1,
    )

    names = {m.test_name for m in measurements}
    assert "HbA1c" in names
    assert "Fasting Blood Glucose" in names
    assert "Serum Creatinine" in names
    assert "eGFR" in names
    assert "Total Cholesterol" in names
    assert "Systolic Blood Pressure" in names
    assert "Diastolic Blood Pressure" in names

    # Verify exact values matched
    hba1c_item = next(m for m in measurements if m.test_name == "HbA1c")
    assert hba1c_item.value == 7.4
    assert hba1c_item.unit == "%"
    assert hba1c_item.report_name == "Spring Clinical Note"
    assert hba1c_item.page_number == 1


def test_fastapi_rest_trend_endpoints(client):
    """
    Test full REST API execution for trend analysis.
    """
    # 1. GET /health
    r_health = client.get("/api/v1/trends/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    # 2. GET /supported-markers
    r_catalog = client.get("/api/v1/trends/supported-markers")
    assert r_catalog.status_code == 200
    catalog = r_catalog.json()
    assert "HbA1c" in catalog
    assert "eGFR" in catalog

    # 3. POST /analyze with raw report texts
    payload = {
        "patient_id": "PATIENT-REST-01",
        "raw_reports": [
            {
                "text": "Laboratory Report: HbA1c = 8.5%",
                "report_name": "Hospital Lab Jan",
                "report_date": "2026-01-10",
                "page_number": 1,
            },
            {
                "text": "Followup Lab: HbA1c = 7.1%",
                "report_name": "Hospital Lab Apr",
                "report_date": "2026-04-10",
                "page_number": 1,
            },
            {
                "text": "Endocrinology Review: HbA1c = 6.3%",
                "report_name": "Hospital Lab Jul",
                "report_date": "2026-07-10",
                "page_number": 1,
            },
        ],
    }

    r_analyze = client.post("/api/v1/trends/analyze", json=payload)
    assert r_analyze.status_code == 200
    data = r_analyze.json()
    assert data["patient_id"] == "PATIENT-REST-01"
    assert "HbA1c" in data["marker_trends"]
    assert data["marker_trends"]["HbA1c"]["direction"] == "IMPROVING"
    assert len(data["trend_graphs"]) == 1
    assert "<svg" in data["trend_graphs"][0]["svg_render"]
    assert len(data["citations"]) == 3
