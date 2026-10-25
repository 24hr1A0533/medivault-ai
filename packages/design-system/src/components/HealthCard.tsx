import React from "react";
import { tokens } from "../tokens";
import { Card } from "./Card";

export interface HealthCardProps {
  title: string;
  category: "Condition" | "Medication" | "Allergy" | "Procedure";
  subtitle: string;
  statusBadge?: string;
  notes?: string;
}

export const HealthCard: React.FC<HealthCardProps> = ({
  title,
  category,
  subtitle,
  statusBadge = "ACTIVE",
  notes,
}) => {
  return (
    <Card accentColor={tokens.colors.brandPrimary} style={{ marginBottom: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.5px", color: tokens.colors.brandSecondary, fontWeight: 700 }}>
            {category}
          </span>
          <div style={{ fontSize: "1.0625rem", fontWeight: 700, color: tokens.colors.textPrimary, marginTop: "2px" }}>
            {title}
          </div>
          <div style={{ fontSize: "0.8125rem", color: tokens.colors.textSecondary, marginTop: "2px" }}>
            {subtitle}
          </div>
        </div>
        <span
          style={{
            padding: "2px 8px",
            borderRadius: tokens.radii.full,
            fontSize: "0.75rem",
            fontWeight: 700,
            backgroundColor: statusBadge === "ACTIVE" ? tokens.colors.brandLight : "#F1F5F9",
            color: statusBadge === "ACTIVE" ? tokens.colors.brandPrimary : tokens.colors.textSecondary,
          }}
        >
          {statusBadge}
        </span>
      </div>
      {notes && (
        <div style={{ marginTop: "10px", fontSize: "0.8125rem", color: tokens.colors.textSecondary, borderTop: `1px solid #F1F5F9`, paddingTop: "8px" }}>
          {notes}
        </div>
      )}
    </Card>
  );
};
