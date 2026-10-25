import React, { useEffect, useState } from "react";
import { fetchPatientProfile, PatientRecord } from "./services/api";

export const PatientPortalApp: React.FC = () => {
  const [profile, setProfile] = useState<PatientRecord | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "timeline" | "meds">("overview");

  useEffect(() => {
    fetchPatientProfile("p-1001").then(setProfile);
  }, []);

  if (!profile) return <div style={{ padding: 24, fontFamily: "sans-serif" }}>Loading patient health vault...</div>;

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", backgroundColor: "#F8FAFC", minHeight: "100vh" }}>
      {/* Top Navigation */}
      <header style={{ backgroundColor: "#0F766E", color: "#FFF", padding: "16px 32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: "1.25rem", fontWeight: 700 }}>MediVault AI Patient Portal</div>
        <div style={{ fontSize: "0.875rem" }}>{profile.name} (MRN: {profile.mrn})</div>
      </header>

      {/* Tabs */}
      <nav style={{ display: "flex", gap: 16, backgroundColor: "#FFF", borderBottom: "1px solid #E2E8F0", padding: "0 32px" }}>
        {(["overview", "timeline", "meds"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "14px 18px",
              border: "none",
              background: "none",
              borderBottom: activeTab === tab ? "3px solid #0F766E" : "3px solid transparent",
              color: activeTab === tab ? "#0F766E" : "#64748B",
              fontWeight: 600,
              cursor: "pointer",
              textTransform: "capitalize",
            }}
          >
            {tab}
          </button>
        ))}
      </nav>

      {/* Body Content */}
      <main style={{ maxWidth: "1200px", margin: "24px auto", padding: "0 24px" }}>
        {activeTab === "overview" && (
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "24px" }}>
            <section style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 24, border: "1px solid #E2E8F0" }}>
              <h2 style={{ fontSize: "1.125rem", color: "#0F172A", marginTop: 0 }}>Recent Lab Findings</h2>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #E2E8F0", textAlign: "left", color: "#64748B" }}>
                    <th style={{ padding: 8 }}>Test</th>
                    <th style={{ padding: 8 }}>Value</th>
                    <th style={{ padding: 8 }}>Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.recentLabs.map((l, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #F1F5F9" }}>
                      <td style={{ padding: 8, fontWeight: 500 }}>{l.marker}</td>
                      <td style={{ padding: 8, color: l.isAbnormal ? "#DC2626" : "#0F172A", fontWeight: 600 }}>
                        {l.value} {l.unit}
                      </td>
                      <td style={{ padding: 8, color: "#64748B" }}>{l.range}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <aside style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 24, border: "1px solid #E2E8F0" }}>
              <h2 style={{ fontSize: "1.125rem", color: "#0F172A", marginTop: 0 }}>Active Allergies</h2>
              {profile.allergies.map((a, i) => (
                <div key={i} style={{ backgroundColor: "#FEF2F2", color: "#991B1B", padding: "8px 12px", borderRadius: 4, marginBottom: 8, fontWeight: 600, fontSize: "0.875rem" }}>
                  {a}
                </div>
              ))}
            </aside>
          </div>
        )}

        {activeTab === "meds" && (
          <div style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 24, border: "1px solid #E2E8F0" }}>
            <h2 style={{ fontSize: "1.125rem", color: "#0F172A", marginTop: 0 }}>Prescription Adherence List</h2>
            {profile.medications.map((m, i) => (
              <div key={i} style={{ borderLeft: "4px solid #0F766E", paddingLeft: 12, marginBottom: 16 }}>
                <div style={{ fontWeight: 700, color: "#0F172A" }}>{m.name} ({m.dosage})</div>
                <div style={{ fontSize: "0.8125rem", color: "#64748B" }}>{m.frequency}</div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default PatientPortalApp;
