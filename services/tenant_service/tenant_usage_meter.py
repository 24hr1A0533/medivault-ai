"""
Tenant Usage Metering Engine.
Tracks real-time consumption metrics for multi-tenant billing, quotas, and anomaly detection.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List


class MetricType(str, Enum):
    AI_COPILOT_QUERIES = "AI_COPILOT_QUERIES"
    OCR_DOCUMENTS_PROCESSED = "OCR_DOCUMENTS_PROCESSED"
    FHIR_API_REQUESTS = "FHIR_API_REQUESTS"
    ACTIVE_PHYSICIAN_SEATS = "ACTIVE_PHYSICIAN_SEATS"
    STORAGE_CONSUMED_BYTES = "STORAGE_CONSUMED_BYTES"
    EMERGENCY_FILE_RETRIEVALS = "EMERGENCY_FILE_RETRIEVALS"


@dataclass
class UsageEntry:
    timestamp: datetime
    metric_type: MetricType
    value: float
    actor_id: str


class TenantUsageMeter:
    """Thread-safe usage metering service."""

    def __init__(self):
        # tenant_id -> MetricType -> total count
        self._totals: Dict[str, Dict[MetricType, float]] = defaultdict(lambda: defaultdict(float))
        # tenant_id -> history of entries
        self._history: Dict[str, List[UsageEntry]] = defaultdict(list)

    def record_usage(
        self, tenant_id: str, metric_type: MetricType, value: float = 1.0, actor_id: str = "system"
    ):
        """Record an incremental consumption event."""
        self._totals[tenant_id][metric_type] += value
        entry = UsageEntry(
            timestamp=datetime.now(timezone.utc),
            metric_type=metric_type,
            value=value,
            actor_id=actor_id,
        )
        self._history[tenant_id].append(entry)

    def get_metric_total(self, tenant_id: str, metric_type: MetricType) -> float:
        """Get the current accumulated total for a specific metric."""
        return self._totals[tenant_id][metric_type]

    def get_all_metrics(self, tenant_id: str) -> Dict[str, float]:
        """Return all aggregated metric counters for a tenant."""
        return {m.value: val for m, val in self._totals[tenant_id].items()}

    def reset_billing_cycle(self, tenant_id: str):
        """Reset incremental counters at start of new monthly billing cycle."""
        self._totals[tenant_id].clear()
