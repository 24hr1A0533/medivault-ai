import React from "react";
import { tokens } from "../tokens";

export type UrgencyTier =
  | "EMERGENCY_CARE_NEEDED"
  | "HOSPITAL_VISIT_RECOMMENDED"
  | "CLINIC_VISIT_RECOMMENDED"
  | "MONITOR_AND_OBSERVE";

export interface TriagePanelProps {
  urgencyTier: UrgencyTier;
  confidenceScore: number;
  clinicalReasoning: string;
  recommendedAction: string;
}

export const TriagePanel: React.FC<TriagePanelProps> = ({
  urgencyTier,
  confidenceScore,
  clinicalReasoning,
  recommendedAction,
}) => {
  const getTierConfig = (tier: UrgencyTier) => {
    switch (tier) {
      case "EMERGENCY_CARE_NEEDED":
        return { label: "TIER 1: EMERGENCY CARE NEEDED", color: tokens.colors.clinicalEmergency, bg: "#FEF2F2" };
      case "HOSPITAL_VISIT_RECOMMENDED":
        return { label: "TIER 2: HOSPITAL VISIT RECOMMENDED", color: tokens.colors.clinicalWarning, bg: "#FFFBEB" };
      case "CLINIC_VISIT_RECOMMENDED":
        return { label: "TIER 3: CLINIC VISIT RECOMMENDED", color: tokens.colors.clinicalInfo, bg: "#EFF6FF" };
      case "MONITOR_AND_OBSERVE":
        return { label: "TIER 4: MONITOR & OBSERVE", color: tokens.colors.clinicalSuccess, bg: "#F0FDF4" };
    }
  };

  const config = getTierConfig(urgencyTier);

  return (
    <div
      style={{
        backgroundColor: config.bg,
        border: `2px solid ${config.color}`,
        borderRadius: tokens.radii.lg,
        padding: "18px",
        marginBottom: "16px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontWeight: 800, fontSize: "1rem", color: config.color, letterSpacing: "0.5px" }}>
          {config.label}
        </div>
        <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: tokens.colors.textSecondary }}>
          Confidence: {(confidenceScore * 100).toFixed(1)}%
        </div>
      </div>
      <div style={{ marginTop: "8px", fontSize: "0.875rem", color: tokens.colors.textPrimary, lineHeight: "1.4" }}>
        <strong>Clinical Assessment:</strong> {clinicalReasoning}
      </div>
      <div style={{ marginTop: "8px", fontSize: "0.875rem", color: config.color, fontWeight: 600 }}>
        Action Protocol: {recommendedAction}
      </div>
    </div>
  );
};
