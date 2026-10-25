import React from "react";
import { tokens } from "../tokens";

export interface AlertProps {
  severity: "critical" | "warning" | "info" | "success";
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const Alert: React.FC<AlertProps> = ({
  severity,
  title,
  message,
  actionLabel,
  onAction,
}) => {
  const styles: Record<string, { bg: string; border: string; color: string }> = {
    critical: {
      bg: "#FEF2F2",
      border: tokens.colors.clinicalEmergency,
      color: "#991B1B",
    },
    warning: {
      bg: "#FFFBEB",
      border: tokens.colors.clinicalWarning,
      color: "#92400E",
    },
    info: {
      bg: "#EFF6FF",
      border: tokens.colors.clinicalInfo,
      color: "#1E40AF",
    },
    success: {
      bg: "#F0FDF4",
      border: tokens.colors.clinicalSuccess,
      color: "#166534",
    },
  };

  const current = styles[severity];

  return (
    <div
      style={{
        backgroundColor: current.bg,
        borderLeft: `4px solid ${current.border}`,
        borderRadius: tokens.radii.md,
        padding: "14px 18px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "12px",
      }}
    >
      <div>
        <div style={{ fontWeight: 600, fontSize: "0.9375rem", color: current.color }}>
          {title}
        </div>
        <div style={{ fontSize: "0.8125rem", color: current.color, marginTop: "2px" }}>
          {message}
        </div>
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            backgroundColor: current.border,
            color: "#FFFFFF",
            border: "none",
            borderRadius: tokens.radii.sm,
            padding: "6px 12px",
            fontSize: "0.8125rem",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
