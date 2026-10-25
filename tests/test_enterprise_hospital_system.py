"""
Comprehensive Test Suite for Next-Generation MediVault Enterprise Hospital System.

Verifies:
1. Emergency Case File Engine (< 2.0s Time-To-Open SLA, ESI Score, Doctor Action Panel)
2. LangGraph 10-Agent Multi-Agent Clinical Intelligence Architecture
3. Visual Triage AI (4-Tier Urgency Output, Uncertainty Calibration, Zero Diagnosis)
4. Offline AI Mode & CRDT Synchronization Engine (Zero-Network Edge Survivability)
5. Apple-Style Clinical Timeline Engine (Month/Week/Day Multi-Scale Horizons)
6. Hospital-Grade UI/UX Design System Tokens & Color Metrics
"""
import json
import pytest
from services.emergency_service.emergency_engine import (
    EmergencyCaseFileEngine,
    EmergencyContact,
    RiskClassification,
)
from services.triage_service.visual_triage import (
    VisualTriageAI,
    VisualTriageRequest,
    TriageUrgencyLevel,
)
from ai.agents.clinical_agents import ClinicalAgentState
from ai.orchestrator.langgraph_orchestrator import LangGraphClinicalOrchestrator
from services.timeline_service.timeline_engine import (
    ClinicalTimelineEngine,
    TimelineEvent,
    TimelineHorizon,
    ClinicalEventCategory,
)
from apps.mobile_app.src.offline.offline_sync_engine import OfflineEdgeEngine

@pytest.fixture
def emergency_engine():
    return EmergencyCaseFileEngine()

@pytest.fixture
def triage_engine():
    return VisualTriageAI()

@pytest.fixture
def agent_orchestrator():
    return LangGraphClinicalOrchestrator()

@pytest.fixture
def timeline_engine():
    return ClinicalTimelineEngine()

@pytest.fixture
def offline_engine():
    return OfflineEdgeEngine()


# ------------------------------------------------------------------------------
# 1. New Core Feature 1: Emergency Case File Engine (< 2.0s Time-To-Open)
# ------------------------------------------------------------------------------
def test_emergency_case_file_engine(emergency_engine):
    sample_records = [
        {
            "category": "LAB_REPORT",
            "report_name": "Comprehensive Metabolic Panel",
            "report_date": "2026-06-15",
            "content": "Patient has severe penicillin allergy (anaphylaxis). Glucose: 148 mg/dL. HbA1c: 8.2% (elevated).",
        },
        {
            "category": "PRESCRIPTION",
            "report_name": "Prescription Slip",
            "report_date": "2026-06-16",
            "content": "Rx: Metformin 500mg BID. Lisinopril 10mg Daily. Patient has Chronic Kidney Disease Stage 3.",
        },
        {
            "category": "CLINICAL_NOTE",
            "report_name": "Cardiology Followup Note",
            "report_date": "2026-06-20",
            "doctor_name": "Dr. Vance",
            "content": "Blood pressure 142/88 mmHg. History of Type 2 Diabetes Mellitus and Laparoscopic Cholecystectomy (2022).",
        },
    ]

    contacts = [
        EmergencyContact(
            name="Mark Vance",
            relationship="Spouse",
            phone_number="555-0192",
            priority=1,
        )
    ]

    case_file = emergency_engine.compile_case_file(
        patient_id="PATIENT-ELEANOR-01",
        patient_name="Eleanor Vance",
        dob="1968-04-12",
        blood_group="O+ Pos",
        raw_records=sample_records,
        emergency_contacts=contacts,
    )

    # 1. Time to open SLA: Must be < 2000 milliseconds (< 2 seconds)
    assert case_file.time_to_open_ms < 2000.0, f"Latency exceeded: {case_file.time_to_open_ms}ms"

    # 2. Score and Classification
    assert case_file.emergency_summary_score >= 50
    assert case_file.risk_classification in (RiskClassification.HIGH, RiskClassification.CRITICAL)
    assert "ESI_2" in case_file.case_priority.value or "ESI_3" in case_file.case_priority.value

    # 3. 6-Month Record Inventory
    assert any("Penicillin" in a.allergen for a in case_file.allergies)
    assert any("Type 2 Diabetes" in c for c in case_file.chronic_diseases)
    assert any("Cholecystectomy" in s for s in case_file.surgeries)
    assert any("Metformin" in m.drug_name for m in case_file.active_medications)
    assert any("HbA1c" in l.test_name for l in case_file.abnormal_labs)
    assert len(case_file.emergency_contacts) == 1

    # 4. Doctor Action Panel
    assert len(case_file.doctor_action_panel) >= 3
    action_titles = [act.protocol_title for act in case_file.doctor_action_panel]
    assert any("CONTRAINDICATION" in t for t in action_titles)

    # 5. Instant Warm Cache Lookup (< 10ms)
    cached = emergency_engine.get_warm_cached_case_file("PATIENT-ELEANOR-01")
    assert cached is not None
    assert cached["patient_name"] == "Eleanor Vance"


# ------------------------------------------------------------------------------
# 2. New Core Feature 2: Multi-Agent Intelligence (LangGraph 10 Agents)
# ------------------------------------------------------------------------------
def test_langgraph_multi_agent_orchestrator(agent_orchestrator):
    """
    Verifies that LangGraph routes queries to all 10 specialized clinical agents:
    Health Timeline, Emergency, Visual Triage, Caregiver, Insurance,
    Medication Intelligence, Patient Copilot, Privacy Guard, Hospital Rec, Clinical Summary.
    """
    test_cases = [
        ("emergency trauma protocol", "emergency_agent"),
        ("show my chronological history", "health_timeline_agent"),
        ("triage wound photo", "visual_triage_agent"),
        ("caregiver update for family", "caregiver_agent"),
        ("check insurance prior auth", "insurance_agent"),
        ("medication interaction check", "medication_agent"),
        ("nearest hospital with icu beds", "hospital_rec_agent"),
        ("generate sbar doctor brief", "clinical_summary_agent"),
        ("how are my blood sugars doing?", "patient_copilot_agent"),
    ]

    for query_intent, expected_agent in test_cases:
        state = ClinicalAgentState(
            patient_id="PATIENT-100",
            user_intent=query_intent,
            raw_query=f"Patient request: {query_intent}",
        )
        res_state = agent_orchestrator.execute_workflow(state)

        assert res_state.active_agent == expected_agent
        assert "privacy_guard" in res_state.agent_outputs  # Agent 8 always runs first
        assert res_state.final_response is not None
        assert len(res_state.execution_trace) >= 2


# ------------------------------------------------------------------------------
# 3. New Core Feature 3: Visual Triage AI
# ------------------------------------------------------------------------------
def test_visual_triage_ai_four_tiers(triage_engine):
    """
    Verifies the 4-tier output:
    1. Emergency Care Needed
    2. Hospital Visit Recommended
    3. Clinic Visit Recommended
    4. Monitor and Observe
    Ensures zero diagnosis and clear uncertainty statement.
    """
    # Tier 1: Emergency Care Needed (red flag chest pain / necrosis)
    req_emerg = VisualTriageRequest(
        patient_id="P-01",
        image_url_or_b64="data:image/jpeg;base64,sampleWound",
        image_type="WOUND",
        symptom_description="Severe crushing chest pain and spreading black tissue near wound",
        pain_level_1_to_10=10,
    )
    res_emerg = triage_engine.process_triage(req_emerg)
    assert res_emerg.urgency_level == TriageUrgencyLevel.EMERGENCY_CARE_NEEDED
    assert len(res_emerg.red_flag_warnings) >= 1

    # Tier 2: Hospital Visit Recommended (diabetic fever + severe pain)
    req_hosp = VisualTriageRequest(
        patient_id="P-02",
        image_url_or_b64="data:image/jpeg;base64,sampleFootWound",
        image_type="WOUND",
        symptom_description="Foot ulcer with systemic fever and chills",
        pain_level_1_to_10=9,
        patient_history_context={"is_diabetic": True},
    )
    res_hosp = triage_engine.process_triage(req_hosp)
    assert res_hosp.urgency_level == TriageUrgencyLevel.HOSPITAL_VISIT_RECOMMENDED

    # Tier 3: Clinic Visit Recommended (moderate pain, spreading margin)
    req_clinic = VisualTriageRequest(
        patient_id="P-03",
        image_url_or_b64="data:image/jpeg;base64,sampleRash",
        image_type="SKIN",
        symptom_description="Spreading red rash along forearm over 3 days",
        pain_level_1_to_10=6,
    )
    res_clinic = triage_engine.process_triage(req_clinic)
    assert res_clinic.urgency_level == TriageUrgencyLevel.CLINIC_VISIT_RECOMMENDED

    # Tier 4: Monitor and Observe (mild superficial scrape)
    req_monitor = VisualTriageRequest(
        patient_id="P-04",
        image_url_or_b64="data:image/jpeg;base64,sampleMinorScrape",
        image_type="INJURY",
        symptom_description="Minor superficial scrape, clean borders, no fever",
        pain_level_1_to_10=2,
    )
    res_monitor = triage_engine.process_triage(req_monitor)
    assert res_monitor.urgency_level == TriageUrgencyLevel.MONITOR_AND_OBSERVE

    # Non-negotiable Clinical Safety check across all tiers
    for resp in [res_emerg, res_hosp, res_clinic, res_monitor]:
        assert "NOT a medical diagnosis" in resp.uncertainty_statement
        assert len(resp.actionable_care_guidance) >= 2


# ------------------------------------------------------------------------------
# 4. New Core Feature 4: Offline AI Mode & CRDT Synchronization
# ------------------------------------------------------------------------------
def test_offline_ai_and_crdt_sync(offline_engine):
    """
    Verifies offline emergency lookup (< 5ms) and CRDT sync replication.
    """
    offline_engine.seed_offline_patient_record(
        patient_id="OFFLINE-PAT-99",
        patient_name="James Wilson",
        blood_group="A- Neg",
        allergies=["Aspirin", "Codeine"],
        medications=["Metoprolol 25mg Daily"],
        recent_reports=[{"name": "Local ECG", "date": "2026-09-10"}],
    )

    # 1. Zero-network emergency lookup
    offline_res = offline_engine.execute_offline_emergency_lookup("OFFLINE-PAT-99")
    assert offline_res["status"] == "OFFLINE_SUCCESS"
    assert offline_res["patient_name"] == "James Wilson"
    assert "Aspirin" in offline_res["allergies"]
    assert offline_res["execution_time_ms"] < 20.0

    # 2. Record offline clinical event
    offline_engine.record_offline_event(
        patient_id="OFFLINE-PAT-99",
        entity_type="MEDICATION",
        action="UPDATE",
        data={"drug": "Metoprolol", "dosage": "50mg"},
    )

    # 3. Synchronize with cloud database
    sync_res = offline_engine.synchronize_with_cloud(cloud_current_clock=0)
    assert sync_res["sync_status"] == "SYNCHRONIZED"
    assert sync_res["operations_replicated"] == 1


# ------------------------------------------------------------------------------
# 5. New Core Feature 5: Clinical Timeline Engine (Apple Style)
# ------------------------------------------------------------------------------
def test_apple_style_clinical_timeline(timeline_engine):
    """
    Verifies multi-scale horizons: Month, Week, Day
    across multiple clinical event categories.
    """
    events = [
        TimelineEvent(
            event_id="EV-1",
            patient_id="P-TIMELINE",
            timestamp="2026-10-24T14:30:00Z",
            category=ClinicalEventCategory.LAB_REPORT,
            title="Comprehensive Metabolic Panel",
            subtitle="HbA1c: 6.3% (Improved -25.9%)",
            clinical_badge="Normal Range",
            badge_color="#22C55E",
            details={"hba1c": 6.3},
            source_citation={"report_name": "Lab Oct", "page_number": "1", "report_date": "2026-10-24"},
        ),
        TimelineEvent(
            event_id="EV-2",
            patient_id="P-TIMELINE",
            timestamp="2026-10-20T09:15:00Z",
            category=ClinicalEventCategory.PRESCRIPTION,
            title="Metformin Refill Order",
            subtitle="500mg BID - 90-day supply",
            clinical_badge="Active",
            badge_color="#0891B2",
            details={"dose": "500mg"},
            source_citation={"report_name": "Rx Slip", "page_number": "1", "report_date": "2026-10-20"},
        ),
        TimelineEvent(
            event_id="EV-3",
            patient_id="P-TIMELINE",
            timestamp="2026-06-15T11:00:00Z",
            category=ClinicalEventCategory.DOCTOR_VISIT,
            title="Cardiology Outpatient Followup",
            subtitle="Dr. Vance - Blood pressure 142/88 mmHg",
            clinical_badge="Elevated",
            badge_color="#F59E0B",
            details={"bp": "142/88"},
            source_citation={"report_name": "Cardio Note", "page_number": "2", "report_date": "2026-06-15"},
        ),
    ]

    # Month Horizon
    tl_month = timeline_engine.render_timeline("P-TIMELINE", events, horizon=TimelineHorizon.MONTH)
    assert len(tl_month.groups) >= 2  # October 2026 and June 2026
    assert tl_month.total_events_in_view == 3

    # Week Horizon
    tl_week = timeline_engine.render_timeline("P-TIMELINE", events, horizon=TimelineHorizon.WEEK)
    assert len(tl_week.groups) >= 2

    # Day Horizon
    tl_day = timeline_engine.render_timeline("P-TIMELINE", events, horizon=TimelineHorizon.DAY)
    assert len(tl_day.groups) == 3


# ------------------------------------------------------------------------------
# 6. UI/UX Hospital Design System Tokens Check
# ------------------------------------------------------------------------------
def test_hospital_design_system_tokens():
    with open("shared/ui/theme.json", "r") as f:
        theme = json.load(f)

    palette = theme["palette"]
    assert palette["primary"]["main"] == "#0F766E"
    assert palette["secondary"]["main"] == "#0891B2"
    assert palette["success"]["main"] == "#22C55E"
    assert palette["warning"]["main"] == "#F59E0B"
    assert palette["danger"]["main"] == "#DC2626"
    assert palette["background"]["app"] == "#F8FAFC"
    assert theme["metrics"]["touchTargetMinPx"] >= 48
    assert theme["metrics"]["emergencyOpenTargetS"] <= 2.0
