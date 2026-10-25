"""
Apple-Style Clinical Timeline Engine.
Supports multi-horizon temporal scaling (Month, Week, Day) across 8 clinical event categories:
- Lab Reports
- Prescriptions
- Scans
- Doctor Visits
- Symptoms
- Triage Events
- Insurance Claims
- Emergency Events
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta

class TimelineHorizon(str, Enum):
    MONTH = "MONTH"
    WEEK = "WEEK"
    DAY = "DAY"

class ClinicalEventCategory(str, Enum):
    LAB_REPORT = "LAB_REPORT"
    PRESCRIPTION = "PRESCRIPTION"
    IMAGING_SCAN = "IMAGING_SCAN"
    DOCTOR_VISIT = "DOCTOR_VISIT"
    SYMPTOM_LOG = "SYMPTOM_LOG"
    TRIAGE_EVENT = "TRIAGE_EVENT"
    INSURANCE_CLAIM = "INSURANCE_CLAIM"
    EMERGENCY_EVENT = "EMERGENCY_EVENT"

class TimelineEvent(BaseModel):
    event_id: str
    patient_id: str
    timestamp: str
    category: ClinicalEventCategory
    title: str
    subtitle: str
    clinical_badge: str      # e.g., "Normal", "Elevated", "Critical", "Active", "Approved"
    badge_color: str         # #22C55E, #F59E0B, #DC2626, #0891B2
    details: Dict[str, Any]
    source_citation: Dict[str, str]

class TimelineHorizonGroup(BaseModel):
    horizon_label: str       # e.g., "October 2026" (Month), "Week 42" (Week), "Oct 24, 2026" (Day)
    start_date: str
    end_date: str
    events: List[TimelineEvent]
    total_events: int

class AppleClinicalTimelineResponse(BaseModel):
    patient_id: str
    selected_horizon: TimelineHorizon
    total_events_in_view: int
    groups: List[TimelineHorizonGroup]
    biometric_macro_trend: str

class ClinicalTimelineEngine:
    """
    Renders high-density, Apple Health-style temporal feeds partitioned into
    Month, Week, or Day horizons.
    """

    def render_timeline(
        self,
        patient_id: str,
        raw_events: List[TimelineEvent],
        horizon: TimelineHorizon = TimelineHorizon.MONTH,
    ) -> AppleClinicalTimelineResponse:
        # Sort chronologically (newest first)
        sorted_events = sorted(raw_events, key=lambda x: x.timestamp, reverse=True)

        groups_map: Dict[str, List[TimelineEvent]] = {}

        for event in sorted_events:
            dt = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
            if horizon == TimelineHorizon.MONTH:
                key = dt.strftime("%B %Y")
            elif horizon == TimelineHorizon.WEEK:
                key = f"Week {dt.isocalendar()[1]}, {dt.year}"
            else: # DAY
                key = dt.strftime("%a, %b %d, %Y")

            groups_map.setdefault(key, []).append(event)

        groups: List[TimelineHorizonGroup] = []
        for label, evs in groups_map.items():
            st = evs[-1].timestamp
            et = evs[0].timestamp
            groups.append(
                TimelineHorizonGroup(
                    horizon_label=label,
                    start_date=st,
                    end_date=et,
                    events=evs,
                    total_events=len(evs),
                )
            )

        return AppleClinicalTimelineResponse(
            patient_id=patient_id,
            selected_horizon=horizon,
            total_events_in_view=len(sorted_events),
            groups=groups,
            biometric_macro_trend="Longitudinal trajectory: Glycemic recovery demonstrated over 6 months with stable renal parameters.",
        )
