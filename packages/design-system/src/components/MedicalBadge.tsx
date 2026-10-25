import React from "react";
import { tokens } from "../tokens";

export interface MedicalBadgeProps {
  label: string;
  category?: "Allergy" | "Medication" | "Lab" | "Diagnosis" | "Vital";
  isAbnormal?: boolean;
}

export const MedicalBadge: React.FC<MedicalBadgeProps> = ({
  label,
  category = "Lab",
  isAbnormal = false,
}) => {
  const getBadgeStyle = () => {
    if (isAbnormal) {
      return { bg: "#FEE2E2", color: tokens.colors.clinicalEmergency, border: "#FCA5A5" };
    }
    switch (category) {
      case "Allergy":
        return { bg: "#FEF3C7", color: "#B45309", border: "#FCD34D" };
      case "Medication":
        return { bg: tokens.colors.brandLight, color: tokens.colors.brandPrimary, border: "#99F6E4" };
      case "Diagnosis":
        return { bg: "#E0F2FE", color: tokens.colors.brandSecondary, border: "#BAE6FD" };
      default:
        return { bg: "#F1F5F9", color: tokens.colors.textSecondary, border: "#CBD5E1" };
    }
  };

  const style = getBadgeStyle();

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "3px 8px",
        borderRadius: tokens.radii.full,
        fontSize: "0.75rem",
        fontWeight: 600,
        backgroundColor: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
      }}
    >
      {label}
    </span>
  );
};
