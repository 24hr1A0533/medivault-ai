import React, { useState } from "react";

export const AdminPortalApp: React.FC = () => {
  const [licensedSeats, setLicensedSeats] = useState(1420);
  const auditLogs = [
    { id: "audit_1", time: "12:04:12", user: "dr_jenkins_mayo", action: "READ_PHI", resource: "Patient/p-1001", outcome: "PERMITTED" },
    { id: "audit_2", time: "12:04:18", user: "ai_copilot_service", action: "QUERY_AI_COPILOT", resource: "DocRef/d-89", outcome: "PERMITTED" },
    { id: "audit_3", time: "12:05:01", user: "nurse_vance_rn", action: "ADMINISTER_MEDICATION", resource: "Med/Metformin", outcome: "PERMITTED" },
  ];

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", backgroundColor: "#F8FAFC", minHeight: "100vh" }}>
      {/* Top Admin Bar */}
      <header style={{ backgroundColor: "#1E293B", color: "#FFF", padding: "16px 32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontWeight: 800, fontSize: "1.125rem" }}>MediVault Enterprise Operations & Compliance</div>
        <div style={{ fontSize: "0.875rem", color: "#94A3B8" }}>Tenant: Mayo Clinic Health Network (ID: mayo-clinic-system)</div>
      </header>

      <main style={{ maxWidth: "1200px", margin: "24px auto", padding: "0 24px" }}>
        {/* KPI Metric Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
          <div style={{ backgroundColor: "#FFF", padding: 20, borderRadius: 8, border: "1px solid #E2E8F0" }}>
            <div style={{ fontSize: "0.75rem", color: "#64748B", fontWeight: 700 }}>LICENSED MD SEATS</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#0F172A", marginTop: 4 }}>{licensedSeats}</div>
            <div style={{ fontSize: "0.75rem", color: "#16A34A" }}>Active & Provisioned</div>
          </div>
          <div style={{ backgroundColor: "#FFF", padding: 20, borderRadius: 8, border: "1px solid #E2E8F0" }}>
            <div style={{ fontSize: "0.75rem", color: "#64748B", fontWeight: 700 }}>STORAGE UTILIZATION</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#0F172A", marginTop: 4 }}>12.4 TB</div>
            <div style={{ fontSize: "0.75rem", color: "#64748B" }}>Of 50 TB Allocated</div>
          </div>
          <div style={{ backgroundColor: "#FFF", padding: 20, borderRadius: 8, border: "1px solid #E2E8F0" }}>
            <div style={{ fontSize: "0.75rem", color: "#64748B", fontWeight: 700 }}>SUBSCRIPTION TIER</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#0F766E", marginTop: 4 }}>ENTERPRISE</div>
            <div style={{ fontSize: "0.75rem", color: "#0F766E" }}>Dedicated VPC + SLA 99.999%</div>
          </div>
          <div style={{ backgroundColor: "#FFF", padding: 20, borderRadius: 8, border: "1px solid #E2E8F0" }}>
            <div style={{ fontSize: "0.75rem", color: "#64748B", fontWeight: 700 }}>AUDIT CHAIN INTEGRITY</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#16A34A", marginTop: 4 }}>VALIDATED</div>
            <div style={{ fontSize: "0.75rem", color: "#16A34A" }}>SHA-256 Tamper Free</div>
          </div>
        </div>

        {/* HIPAA §164.312 WORM Audit Trail */}
        <div style={{ backgroundColor: "#FFF", borderRadius: 8, padding: 24, border: "1px solid #E2E8F0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h2 style={{ fontSize: "1.125rem", color: "#0F172A", margin: 0 }}>
              HIPAA §164.312 WORM Compliance Audit Trail
            </h2>
            <button style={{ backgroundColor: "#0F766E", color: "#FFF", border: "none", padding: "8px 14px", borderRadius: 4, fontWeight: 600, fontSize: "0.8125rem", cursor: "pointer" }}>
              Export Signed Compliance Bundle
            </button>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #E2E8F0", textAlign: "left", color: "#64748B" }}>
                <th style={{ padding: "10px 8px" }}>Event ID</th>
                <th style={{ padding: "10px 8px" }}>Timestamp</th>
                <th style={{ padding: "10px 8px" }}>User Principal</th>
                <th style={{ padding: "10px 8px" }}>Action</th>
                <th style={{ padding: "10px 8px" }}>Resource Target</th>
                <th style={{ padding: "10px 8px" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id} style={{ borderBottom: "1px solid #F1F5F9" }}>
                  <td style={{ padding: "10px 8px", fontFamily: "monospace", color: "#64748B" }}>{log.id}</td>
                  <td style={{ padding: "10px 8px" }}>{log.time}</td>
                  <td style={{ padding: "10px 8px", fontWeight: 600 }}>{log.user}</td>
                  <td style={{ padding: "10px 8px" }}>{log.action}</td>
                  <td style={{ padding: "10px 8px" }}>{log.resource}</td>
                  <td style={{ padding: "10px 8px" }}>
                    <span style={{ backgroundColor: "#DCFCE7", color: "#166534", padding: "2px 6px", borderRadius: 4, fontSize: "0.75rem", fontWeight: 700 }}>
                      {log.outcome}
                    </span>
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

export default AdminPortalApp;
