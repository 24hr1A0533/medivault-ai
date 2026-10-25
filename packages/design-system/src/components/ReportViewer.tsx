import React, { useState } from "react";
import { tokens } from "../tokens";

export interface ReportViewerProps {
  reportTitle: string;
  reportDate: string;
  sourceFileUrl?: string;
  extractedFindings: Array<{ marker: string; value: string; unit: string; range: string; isAbnormal: boolean }>;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  reportTitle,
  reportDate,
  sourceFileUrl,
  extractedFindings,
}) => {
  const [activeTab, setActiveTab] = useState<"extracted" | "original">("extracted");

  return (
    <div
      style={{
        border: `1px solid ${tokens.colors.surfaceBorder}`,
        borderRadius: tokens.radii.lg,
        backgroundColor: tokens.colors.surfacePanel,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 18px",
          borderBottom: `1px solid ${tokens.colors.surfaceBorder}`,
          backgroundColor: tokens.colors.surfaceLight,
        }}
      >
        <div>
          <div style={{ fontWeight: 600, fontSize: "0.9375rem" }}>{reportTitle}</div>
          <div style={{ fontSize: "0.75rem", color: tokens.colors.textSecondary }}>{reportDate}</div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={() => setActiveTab("extracted")}
            style={{
              padding: "6px 12px",
              borderRadius: tokens.radii.sm,
              border: "none",
              backgroundColor: activeTab === "extracted" ? tokens.colors.brandPrimary : "transparent",
              color: activeTab === "extracted" ? "#FFF" : tokens.colors.textSecondary,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Structured Data
          </button>
          <button
            onClick={() => setActiveTab("original")}
            style={{
              padding: "6px 12px",
              borderRadius: tokens.radii.sm,
              border: "none",
              backgroundColor: activeTab === "original" ? tokens.colors.brandPrimary : "transparent",
              color: activeTab === "original" ? "#FFF" : tokens.colors.textSecondary,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Original Document
          </button>
        </div>
      </div>

      <div style={{ padding: "18px" }}>
        {activeTab === "extracted" ? (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${tokens.colors.surfaceBorder}`, textAlign: "left", color: tokens.colors.textSecondary }}>
                <th style={{ padding: "8px" }}>Biomarker</th>
                <th style={{ padding: "8px" }}>Value</th>
                <th style={{ padding: "8px" }}>Ref Range</th>
                <th style={{ padding: "8px" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {extractedFindings.map((f, i) => (
                <tr key={i} style={{ borderBottom: `1px solid #F1F5F9` }}>
                  <td style={{ padding: "8px", fontWeight: 500 }}>{f.marker}</td>
                  <td style={{ padding: "8px", fontFamily: tokens.typography.fontMono, fontWeight: 600, color: f.isAbnormal ? tokens.colors.clinicalEmergency : tokens.colors.textPrimary }}>
                    {f.value} {f.unit}
                  </td>
                  <td style={{ padding: "8px", color: tokens.colors.textSecondary }}>{f.range}</td>
                  <td style={{ padding: "8px" }}>
                    <span
                      style={{
                        padding: "2px 6px",
                        borderRadius: tokens.radii.sm,
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        backgroundColor: f.isAbnormal ? "#FEE2E2" : "#DCFCE7",
                        color: f.isAbnormal ? tokens.colors.clinicalEmergency : tokens.colors.clinicalSuccess,
                      }}
                    >
                      {f.isAbnormal ? "ABNORMAL" : "NORMAL"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ height: "300px", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "#F8FAFC", color: tokens.colors.textSecondary }}>
            {sourceFileUrl ? `Document Stream: ${sourceFileUrl}` : "Clinical PDF / Image Preview Available via WADO-RS"}
          </div>
        )}
      </div>
    </div>
  );
};
