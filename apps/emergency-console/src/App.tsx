import React, { useState } from "react";

export const EmergencyConsoleApp: React.FC = () => {
  const [breakGlassActivated, setBreakGlassActivated] = useState(false);

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", backgroundColor: "#090D16", color: "#F8FAFC", minHeight: "100vh", padding: 24 }}>
      {/* Trauma Bay Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #1E293B", paddingBottom: 16 }}>
        <div>
          <span style={{ backgroundColor: "#DC2626", color: "#FFF", padding: "4px 10px", borderRadius: 4, fontWeight: 800, fontSize: "0.875rem", letterSpacing: "1px" }}>
            LEVEL 1 TRAUMA CONSOLE
          </span>
          <span style={{ marginLeft: 16, fontSize: "1.125rem", fontWeight: 700 }}>
            BED: RESUS-01 | ETA: 2 MINS
          </span>
        </div>
        <div style={{ fontFamily: "monospace", fontSize: "0.875rem", color: "#34D399" }}>
          WARM CACHE RETRIEVAL: 1.12s (P99 SLA: < 2.0s)
        </div>
      </div>

      {/* Critical Red Diamond Warning Banner */}
      <div style={{ marginTop: 24, backgroundColor: "#1E1116", border: "2px solid #DC2626", borderRadius: 8, padding: 20 }}>
        <div style={{ fontSize: "0.8125rem", color: "#F87171", fontWeight: 700, textTransform: "uppercase", letterSpacing: "1px" }}>
          ACUTE RESUSCITATION DIAMOND (CONFIRMED)
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginTop: 12 }}>
          <div>
            <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>CODE STATUS</div>
            <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#FFF" }}>FULL CODE</div>
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>BLOOD TYPE</div>
            <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#38BDF8" }}>O-NEGATIVE</div>
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>ALLERGIES</div>
            <div style={{ fontSize: "1.125rem", fontWeight: 800, color: "#EF4444" }}>PENICILLIN (Anaphylaxis)</div>
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>ACTIVE ANTICOAGULANT</div>
            <div style={{ fontSize: "1.125rem", fontWeight: 800, color: "#F59E0B" }}>APIXABAN (Eliquis) 5mg</div>
          </div>
        </div>
      </div>

      {/* Trauma Vitals & Shock Index */}
      <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
        <div style={{ backgroundColor: "#131B2E", padding: 16, borderRadius: 8, border: "1px solid #1E293B" }}>
          <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>BLOOD PRESSURE</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#EF4444" }}>82 / 54</div>
          <div style={{ fontSize: "0.75rem", color: "#EF4444" }}>Hypotensive Crisis</div>
        </div>
        <div style={{ backgroundColor: "#131B2E", padding: 16, borderRadius: 8, border: "1px solid #1E293B" }}>
          <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>HEART RATE</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#EF4444" }}>128 bpm</div>
          <div style={{ fontSize: "0.75rem", color: "#EF4444" }}>Sinus Tachycardia</div>
        </div>
        <div style={{ backgroundColor: "#131B2E", padding: 16, borderRadius: 8, border: "1px solid #1E293B" }}>
          <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>SHOCK INDEX (HR/SBP)</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#EF4444" }}>1.56</div>
          <div style={{ fontSize: "0.75rem", color: "#EF4444" }}>Severe Shock (> 1.0)</div>
        </div>
        <div style={{ backgroundColor: "#131B2E", padding: 16, borderRadius: 8, border: "1px solid #1E293B" }}>
          <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>GLASGOW COMA SCALE</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#F59E0B" }}>11 (E3 V3 M5)</div>
          <div style={{ fontSize: "0.75rem", color: "#F59E0B" }}>Moderate Impairment</div>
        </div>
      </div>

      {/* Immediate Clinical Action Protocol */}
      <div style={{ marginTop: 24, backgroundColor: "#131B2E", padding: 20, borderRadius: 8, border: "1px solid #1E293B" }}>
        <h3 style={{ margin: "0 0 12px 0", fontSize: "1rem", color: "#38BDF8" }}>Acute Resuscitation Protocol Checklist</h3>
        <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.875rem", lineHeight: "1.8", color: "#CBD5E1" }}>
          <li>Activate Massive Transfusion Protocol (Pack: 4 Units O-Neg PRBCs + 4 Units FFP).</li>
          <li>Prepare Factor Xa reversal agent (Andexanet Alfa) due to active Apixaban therapy.</li>
          <li>Contraindicated: Ampicillin / Piperacillin-Tazobactam (Severe Penicillin Allergy). Substitute Meropenem or Ciprofloxacin.</li>
        </ul>
        <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
          <button
            onClick={() => setBreakGlassActivated(!breakGlassActivated)}
            style={{
              backgroundColor: breakGlassActivated ? "#16A34A" : "#DC2626",
              color: "#FFF",
              border: "none",
              padding: "10px 20px",
              borderRadius: 6,
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {breakGlassActivated ? "BREAK-GLASS RECORD OVERRIDE ACTIVE" : "ACTIVATE BREAK-GLASS OVERRIDE"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmergencyConsoleApp;
