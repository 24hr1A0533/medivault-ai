import React from "react";
import { tokens } from "../tokens";

export interface VitalsData {
  bloodPressure: string;
  heartRate: number;
  respiratoryRate: number;
  spO2: number;
  temperature: number;
  lastUpdated: string;
}

export const VitalsPanel: React.FC<{ vitals: VitalsData }> = ({ vitals }) => {
  const isBPAbnormal = () => {
    const parts = vitals.bloodPressure.split("/");
    if (parts.length === 2) {
      const systolic = parseInt(parts[0]);
      return systolic > 140 || systolic < 90;
    }
    return false;
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
        gap: "12px",
        padding: "16px",
        backgroundColor: tokens.colors.surfaceLight,
        borderRadius: tokens.radii.lg,
        border: `1px solid ${tokens.colors.surfaceBorder}`,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "0.75rem", color: tokens.colors.textSecondary }}>BLOOD PRESSURE</div>
        <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: tokens.typography.fontMono, color: isBPAbnormal() ? tokens.colors.clinicalEmergency : tokens.colors.textPrimary }}>
          {vitals.bloodPressure}
        </div>
        <div style={{ fontSize: "0.7rem", color: tokens.colors.textSecondary }}>mmHg</div>
      </div>

      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "0.75rem", color: tokens.colors.textSecondary }}>HEART RATE</div>
        <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: tokens.typography.fontMono, color: vitals.heartRate > 100 || vitals.heartRate < 50 ? tokens.colors.clinicalEmergency : tokens.colors.textPrimary }}>
          {vitals.heartRate}
        </div>
        <div style={{ fontSize: "0.7rem", color: tokens.colors.textSecondary }}>bpm</div>
      </div>

      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "0.75rem", color: tokens.colors.textSecondary }}>OXYGEN (SpO2)</div>
        <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: tokens.typography.fontMono, color: vitals.spO2 < 94 ? tokens.colors.clinicalEmergency : tokens.colors.textPrimary }}>
          {vitals.spO2}%
        </div>
        <div style={{ fontSize: "0.7rem", color: tokens.colors.textSecondary }}>Room Air</div>
      </div>

      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "0.75rem", color: tokens.colors.textSecondary }}>TEMPERATURE</div>
        <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: tokens.typography.fontMono, color: vitals.temperature > 100.4 ? tokens.colors.clinicalEmergency : tokens.colors.textPrimary }}>
          {vitals.temperature}°F
        </div>
        <div style={{ fontSize: "0.7rem", color: tokens.colors.textSecondary }}>Oral</div>
      </div>
    </div>
  );
};
