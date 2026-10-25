import React, { useState } from "react";

interface MARItem {
  id: string;
  drug: string;
  dose: string;
  route: string;
  scheduledTime: string;
  status: "DUE" | "GIVEN" | "HELD";
}

export const NurseConsoleApp: React.FC = () => {
  const [patientVerified, setPatientVerified] = useState(false);
  const [meds, setMeds] = useState<MARItem[]>([
    { id: "1", drug: "Metformin HCl", dose: "500mg", route: "Oral", scheduledTime: "12:00", status: "DUE" },
    { id: "2", drug: "Furosemide (Lasix)", dose: "40mg", route: "IV Push", scheduledTime: "12:00", status: "DUE" },
    { id: "3", drug: "Atorvastatin Calcium", dose: "20mg", route: "Oral", scheduledTime: "21:00", status: "DUE" },
  ]);

  const handleAdminister = (id: string) => {
    setMeds((prev) =>
      prev.map((m) => (m.id === id ? { ...m, status: "GIVEN" } : m))
    );
  };

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", backgroundColor: "#F8FAFC", minHeight: "100vh" }}>
      {/* Top Station Bar */}
      <header style={{ backgroundColor: "#0284C7", color: "#FFF", padding: "14px 28px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontWeight: 800, fontSize: "1.125rem" }}>MediVault Nurse Station: 4-West (Cardio Ward)</div>
        <div style={{ fontSize: "0.875rem" }}>Nurse: K. Vance, RN</div>
      </header>

      <main style={{ maxWidth: "1100px", margin: "24px auto", padding: "0 24px" }}>
        {/* Bedside Patient Verification Barcode Scanner */}
        <div style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 20, border: "1px solid #E2E8F0", marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: "0.8125rem", color: "#64748B", textTransform: "uppercase", fontWeight: 700 }}>
              Bedside Patient Verification (BCMA)
            </div>
            <div style={{ fontSize: "1.125rem", fontWeight: 700, color: "#0F172A", marginTop: 4 }}>
              Bed 412-B: DOE, JOHN (MRN #8920192)
            </div>
          </div>
          <button
            onClick={() => setPatientVerified(true)}
            style={{
              backgroundColor: patientVerified ? "#16A34A" : "#0284C7",
              color: "#FFF",
              border: "none",
              padding: "10px 18px",
              borderRadius: 6,
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {patientVerified ? "✓ Wristband Scanned & Verified" : "Scan Patient Wristband"}
          </button>
        </div>

        {/* 5-Rights Electronic Medication Administration Record (eMAR) */}
        <div style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 24, border: "1px solid #E2E8F0" }}>
          <h2 style={{ fontSize: "1.125rem", color: "#0F172A", margin: "0 0 16px 0" }}>
            Scheduled 12:00 eMAR Medication Administration (5 Rights Check)
          </h2>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #E2E8F0", textAlign: "left", color: "#64748B" }}>
                <th style={{ padding: "10px 8px" }}>Medication</th>
                <th style={{ padding: "10px 8px" }}>Dose</th>
                <th style={{ padding: "10px 8px" }}>Route</th>
                <th style={{ padding: "10px 8px" }}>Scheduled</th>
                <th style={{ padding: "10px 8px" }}>Status</th>
                <th style={{ padding: "10px 8px" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {meds.map((m) => (
                <tr key={m.id} style={{ borderBottom: "1px solid #F1F5F9" }}>
                  <td style={{ padding: "10px 8px", fontWeight: 600 }}>{m.drug}</td>
                  <td style={{ padding: "10px 8px" }}>{m.dose}</td>
                  <td style={{ padding: "10px 8px" }}>{m.route}</td>
                  <td style={{ padding: "10px 8px" }}>{m.scheduledTime}</td>
                  <td style={{ padding: "10px 8px" }}>
                    <span
                      style={{
                        padding: "3px 8px",
                        borderRadius: 4,
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        backgroundColor: m.status === "GIVEN" ? "#DCFCE7" : "#FEF3C7",
                        color: m.status === "GIVEN" ? "#166534" : "#92400E",
                      }}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td style={{ padding: "10px 8px" }}>
                    {m.status === "DUE" && (
                      <button
                        onClick={() => handleAdminister(m.id)}
                        disabled={!patientVerified}
                        style={{
                          backgroundColor: patientVerified ? "#0F766E" : "#94A3B8",
                          color: "#FFF",
                          border: "none",
                          padding: "6px 12px",
                          borderRadius: 4,
                          fontWeight: 600,
                          cursor: patientVerified ? "pointer" : "not-allowed",
                        }}
                      >
                        Administer (Scan Unit-Dose)
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
};

export default NurseConsoleApp;
