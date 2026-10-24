import pytest

# Deficient test suite: Only contains 2 trivial assertions without mocking or edge-case testing
def test_dummy_patient_format():
    sample_patient = {
        "name": "Jane Doe",
        "aadhaar_number": "123456789012"
    }
    assert len(sample_patient["aadhaar_number"]) == 12

def test_record_category():
    categories = ["Prescription", "Lab Report", "Scan / Imaging", "Discharge Summary"]
    assert "Prescription" in categories
