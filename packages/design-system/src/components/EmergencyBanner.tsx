import React from "react";
import { tokens } from "../tokens";

export interface EmergencyBannerProps {
  allergies: string[];
  codeStatus: string;
  bloodType: string;
  anticoagulant?: string;
  onOverrideBreakGlass?: () => void;
}

export const EmergencyBanner: React.FC<EmergencyBannerProps> = ({
  allergies,
  codeStatus,
  bloodType,
  anticoagulant,
  onOverrideBreakGlass,
}) => {
  return (
    <div
      style={{
        backgroundColor: tokens.colors.clinicalEmergency,
        color: "#FFFFFF",
        padding: "16px 24px",
        borderRadius: tokens.radii.lg,
        boxShadow: `0 4px 14px ${tokens.colors.clinicalEmergencyGlow}`,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "16px",
      }}
    >
      <div>
        <div style={{ fontSize: "0.8125rem", letterSpacing: "1px", textTransform: "uppercase", fontWeight: 700, opacity: 0.9 }}>
          ACUTE RESUSCITATION DIAMOND
        </div>
        <div style={{ fontSize: "1.125rem", fontWeight: 700, marginTop: "4px" }}>
          CODE: {codeStatus} | BLOOD: {bloodType}
        </div>
        <div style={{ fontSize: "0.875rem", marginTop: "4px" }}>
          <strong>ALLERGIES:</strong> {allergies.length ? allergies.join(", ") : "None Documented"}
          {anticoagulant && (
            <span style={{ marginLeft: "12px", background: "rgba(0,0,0,0.25)", padding: "2px 8px", borderRadius: "4px" }}>
              ANTICOAGULANT: {anticoagulant}
            </span>
          )}
        </div>
      </div>
      {onOverrideBreakGlass && (
        <button
          onClick={onOverrideBreakGlass}
          style={{
            backgroundColor: "#FFFFFF",
            color: tokens.colors.clinicalEmergency,
            border: "none",
            borderRadius: tokens.radii.md,
            padding: "10px 18px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          BREAK-GLASS ACCESS
        </button>
      )}
    </div>
  );
};
