import pytest
from inference import predict_diabetes_risk, predict_cardio_risk

def test_diabetes_inference_schema():
    payload = {
        "pregnancies": 2,
        "glucose": 130,
        "blood_pressure": 80,
        "skin_thickness": 20,
        "insulin": 85,
        "bmi": 28.5,
        "diabetes_pedigree": 0.45,
        "age": 45
    }
    res = predict_diabetes_risk(payload)
    assert res["disease"] == "Diabetes"
    assert "risk_score" in res
    assert res["risk_level"] in ["Low", "Moderate", "High"]

def test_missing_feature_raises_keyerror():
    payload = {"glucose": 120}
    with pytest.raises(KeyError):
        predict_diabetes_risk(payload)
