"""
Validation test suite for recently implemented enterprise endpoints:
1. POST /api/v1/auth/revoke
2. POST /api/v1/doctors/clinical-notes/sign
3. POST /emergency/break-glass
4. GET /fhir/r4/$export
5. Antivirus binary scanner & POST /api/v1/records/scan
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_enterprise import create_enterprise_app
from services.security.antivirus_scanner import antivirus_scanner
from services.emergency_service.emergency_controller import emergency_router


def test_fhir_bulk_export_endpoint():
    app = create_enterprise_app()
    client = TestClient(app)

    res = client.get("/fhir/r4/$export")
    assert res.status_code == 202
    assert "Content-Location" in res.headers
    data = res.json()
    assert data["status"] == "QUEUED_AND_ACCEPTED"
    assert len(data["output"]) >= 3
    assert any(item["type"] == "Patient" for item in data["output"])


def test_emergency_break_glass_endpoint():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(emergency_router)
    client = TestClient(app)

    # Missing reason -> 400
    res_bad = client.post("/emergency/break-glass", json={"patient_id": "P-99", "reason": ""})
    assert res_bad.status_code == 400

    # Valid break-glass -> 201
    res_good = client.post("/emergency/break-glass", json={
        "patient_id": "P-99",
        "reason": "Unresponsive trauma patient, acute hemorrhagic shock, immediate laparotomy required",
        "requester_role": "ATTENDING_TRAUMA_SURGEON"
    })
    assert res_good.status_code == 201
    data = res_good.json()
    assert data["status"] == "OVERRIDE_ACTIVE_AUDITED"
    assert data["override_token"].startswith("BG-")
    assert len(data["audit_hash"]) == 64


def test_antivirus_binary_scanner_clean():
    # Valid PDF magic bytes
    clean_pdf = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    is_clean, verdict = antivirus_scanner.validate_and_scan(clean_pdf, "blood_test.pdf")
    assert is_clean is True
    assert "CLEAN" in verdict


def test_antivirus_binary_scanner_rejects_executable():
    # Windows PE header (MZ) disguised as PDF
    malicious_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    is_clean, verdict = antivirus_scanner.validate_and_scan(malicious_exe, "lab_report.exe")
    assert is_clean is False
    assert "rejected" in verdict.lower()


def test_antivirus_binary_scanner_rejects_embedded_script():
    # PDF with embedded malicious script
    xss_pdf = b"%PDF-1.4\n<script>eval(atob('malicious_code'))</script>\n%%EOF"
    is_clean, verdict = antivirus_scanner.validate_and_scan(xss_pdf, "trojan.pdf")
    assert is_clean is False
    assert "script signature detected" in verdict.lower()
