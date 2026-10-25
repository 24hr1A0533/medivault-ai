"""
Tenant Billing and Invoicing Engine.
Calculates monthly and usage-based subscriptions for Patient, Family, Clinic, Hospital, and Enterprise tiers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid
from .tenant_repository import SubscriptionTier


@dataclass
class LineItem:
    description: str
    unit_price: float
    quantity: int
    total_amount: float


@dataclass
class Invoice:
    invoice_id: str
    tenant_id: str
    tier: SubscriptionTier
    billing_period_start: datetime
    billing_period_end: datetime
    base_charge: float
    usage_charge: float
    total_amount_due: float
    currency: str = "USD"
    is_paid: bool = False
    line_items: List[LineItem] = field(default_factory=list)
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


TIER_BASE_PRICES = {
    SubscriptionTier.PATIENT: 9.99,
    SubscriptionTier.FAMILY: 24.99,
    SubscriptionTier.CLINIC: 399.00,
    SubscriptionTier.HOSPITAL: 12500.00,
    SubscriptionTier.ENTERPRISE: 45000.00,
}

OVERAGE_RATES = {
    "per_physician_seat": 50.00,
    "per_1000_ai_queries": 15.00,
    "per_gb_storage": 0.20,
}


class TenantBillingEngine:
    """Manages subscription charges, overage invoices, and payment status."""

    def __init__(self):
        self._invoices: Dict[str, List[Invoice]] = {}

    def generate_monthly_invoice(
        self,
        tenant_id: str,
        tier: SubscriptionTier,
        period_start: datetime,
        period_end: datetime,
        extra_seats: int = 0,
        extra_ai_queries: int = 0,
        extra_storage_gb: int = 0,
    ) -> Invoice:
        base_price = TIER_BASE_PRICES[tier]
        items: List[LineItem] = [
            LineItem(
                description=f"Base Subscription Plan: {tier.value}",
                unit_price=base_price,
                quantity=1,
                total_amount=base_price,
            )
        ]

        usage_charge = 0.0
        if extra_seats > 0:
            seat_charge = extra_seats * OVERAGE_RATES["per_physician_seat"]
            items.append(
                LineItem(
                    description="Additional Licensed Physician Seats",
                    unit_price=OVERAGE_RATES["per_physician_seat"],
                    quantity=extra_seats,
                    total_amount=seat_charge,
                )
            )
            usage_charge += seat_charge

        if extra_ai_queries > 0:
            query_units = extra_ai_queries / 1000.0
            query_charge = query_units * OVERAGE_RATES["per_1000_ai_queries"]
            items.append(
                LineItem(
                    description="Additional AI Copilot Queries (per 1,000)",
                    unit_price=OVERAGE_RATES["per_1000_ai_queries"],
                    quantity=int(query_units),
                    total_amount=query_charge,
                )
            )
            usage_charge += query_charge

        if extra_storage_gb > 0:
            storage_charge = extra_storage_gb * OVERAGE_RATES["per_gb_storage"]
            items.append(
                LineItem(
                    description="Over-quota Medical Record Storage (GB)",
                    unit_price=OVERAGE_RATES["per_gb_storage"],
                    quantity=extra_storage_gb,
                    total_amount=storage_charge,
                )
            )
            usage_charge += storage_charge

        total = round(base_price + usage_charge, 2)
        invoice = Invoice(
            invoice_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
            tenant_id=tenant_id,
            tier=tier,
            billing_period_start=period_start,
            billing_period_end=period_end,
            base_charge=base_price,
            usage_charge=usage_charge,
            total_amount_due=total,
            line_items=items,
        )

        if tenant_id not in self._invoices:
            self._invoices[tenant_id] = []
        self._invoices[tenant_id].append(invoice)
        return invoice

    def get_tenant_invoices(self, tenant_id: str) -> List[Invoice]:
        return self._invoices.get(tenant_id, [])

    def mark_paid(self, invoice_id: str) -> bool:
        for invoices in self._invoices.values():
            for inv in invoices:
                if inv.invoice_id == invoice_id:
                    inv.is_paid = True
                    return True
        return False
