import React, { useState } from "react";

export const DoctorPortalApp: React.FC = () => {
  const [copilotQuery, setCopilotQuery] = useState("");
  const [copilotResponse, setCopilotResponse] = useState<string | null>(null);

  const handleAskCopilot = () => {
    if (!copilotQuery) return;
    setCopilotResponse(
      "Based on Lab Accession #L8921 (Oct 24, 2026), eGFR is stable at 84 mL/min/1.73m2. No dose adjustment needed for Metformin. Penicillin allergy confirmed severe."
    );
  };

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", backgroundColor: "#F1F5F9", minHeight: "100vh" }}>
      {/* Clinician Header Bar */}
      <header style={{ backgroundColor: "#0F172A", color: "#FFF", padding: "14px 28px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontWeight: 800, fontSize: "1.125rem", color: "#14B8A6" }}>MediVault MD</span>
          <span style={{ fontSize: "0.875rem", background: "#334155", padding: "4px 10px", borderRadius: 4 }}>
            PATIENT: DOE, JOHN (58M) | MRN: #8920192 | ROOM: 412-B
          </span>
        </div>
        <div style={{ fontSize: "0.8125rem", color: "#94A3B8" }}>Attending: Dr. Sarah Jenkins, Mayo Clinic</div>
      </header>

      {/* Grid Layout: SBAR & Trends (Left 70%), AI Copilot (Right 30%) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", minHeight: "calc(100vh - 56px)" }}>
        {/* Main Workstation */}
        <main style={{ padding: 24, overflowY: "auto" }}>
          {/* SBAR Brief */}
          <div style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 20, border: "1px solid #CBD5E1", marginBottom: 20 }}>
            <h2 style={{ fontSize: "1rem", color: "#0F172A", margin: "0 0 12px 0", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              SBAR Pre-Rounding Clinical Brief
            </h2>
            <div style={{ fontSize: "0.875rem", lineHeight: "1.6", color: "#334155" }}>
              <p><strong>S (Situation):</strong> 58yo male admitted for atypical chest discomfort and exertional dyspnea.</p>
              <p><strong>B (Background):</strong> T2DM (7 yrs), Hyperlipidemia, ex-smoker. Penicillin allergy (anaphylaxis).</p>
              <p><strong>A (Assessment):</strong> Post-PCI Day 2. Serial troponins flat (< 0.01 ng/mL). Vital signs within target range.</p>
              <p><strong>R (Recommendation):</strong> Discontinue IV telemetry; initiate oral cardiac rehab protocol for 14:00 discharge.</p>
            </div>
            <button style={{ backgroundColor: "#0F766E", color: "#FFF", border: "none", padding: "8px 16px", borderRadius: 4, fontWeight: 600, cursor: "pointer", marginTop: 8 }}>
              Insert Note into EHR Flowsheet
            </button>
          </div>

          {/* Biomarker Trend Matrix */}
          <div style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 20, border: "1px solid #CBD5E1" }}>
            <h2 style={{ fontSize: "1rem", color: "#0F172A", margin: "0 0 12px 0", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Longitudinal Lab Trajectory
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
              <div style={{ padding: 12, backgroundColor: "#F8FAFC", borderRadius: 6, border: "1px solid #E2E8F0" }}>
                <div style={{ fontSize: "0.75rem", color: "#64748B" }}>HbA1c Trajectory</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#16A34A" }}>8.5% → 7.1% → 6.3%</div>
                <div style={{ fontSize: "0.75rem", color: "#16A34A", fontWeight: 600 }}>Consistent Improvement</div>
              </div>
              <div style={{ padding: 12, backgroundColor: "#F8FAFC", borderRadius: 6, border: "1px solid #E2E8F0" }}>
                <div style={{ fontSize: "0.75rem", color: "#64748B" }}>LDL Cholesterol</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#16A34A" }}>142 → 98 → 72 mg/dL</div>
                <div style={{ fontSize: "0.75rem", color: "#16A34A", fontWeight: 600 }}>Statin Goal Achieved</div>
              </div>
              <div style={{ padding: 12, backgroundColor: "#F8FAFC", borderRadius: 6, border: "1px solid #E2E8F0" }}>
                <div style={{ fontSize: "0.75rem", color: "#64748B" }}>Serum Creatinine</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0F172A" }}>0.95 mg/dL</div>
                <div style={{ fontSize: "0.75rem", color: "#64748B" }}>Baseline Stable</div>
              </div>
            </div>
          </div>
        </main>

        {/* AI Copilot Sidecar */}
        <aside style={{ backgroundColor: "#FFF", borderLeft: "1px solid #CBD5E1", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #E2E8F0", backgroundColor: "#F8FAFC" }}>
            <div style={{ fontWeight: 700, fontSize: "0.9375rem", color: "#0F766E" }}>MediVault AI Copilot</div>
            <div style={{ fontSize: "0.75rem", color: "#64748B" }}>Grounded in US Core FHIR + 14 Reports</div>
          </div>

          <div style={{ flex: 1, padding: 16, overflowY: "auto" }}>
            {copilotResponse ? (
              <div style={{ backgroundColor: "#F0FDFA", borderLeft: "3px solid #0F766E", padding: 12, borderRadius: 4, fontSize: "0.8125rem", color: "#134E4A" }}>
                <strong>Clinical Copilot Answer:</strong>
                <p style={{ margin: "6px 0" }}>{copilotResponse}</p>
                <span style={{ fontSize: "0.7rem", color: "#0D9488", fontWeight: 700 }}>Grounding: 99.4% Confidence (Citation #L8921)</span>
              </div>
            ) : (
              <div style={{ color: "#94A3B8", fontSize: "0.8125rem", textAlign: "center", marginTop: 40 }}>
                Query the patient's records using clinical natural language.
              </div>
            )}
          </div>

          <div style={{ padding: 16, borderTop: "1px solid #E2E8F0" }}>
            <input
              type="text"
              placeholder="Ask Copilot (e.g., Check renal dosing)..."
              value={copilotQuery}
              onChange={(e) => setCopilotQuery(e.target.value)}
              style={{ width: "100%", padding: "8px 12px", borderRadius: 4, border: "1px solid #CBD5E1", fontSize: "0.8125rem", marginBottom: 8, boxSizing: "border-box" }}
            />
            <button
              onClick={handleAskCopilot}
              style={{ width: "100%", backgroundColor: "#0F766E", color: "#FFF", border: "none", padding: "8px 0", borderRadius: 4, fontWeight: 600, fontSize: "0.8125rem", cursor: "pointer" }}
            >
              Ask AI Assistant
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default DoctorPortalApp;
