"""
Model inference and preprocessor module.
Security risk: Deserializes joblib files directly without integrity verification (HMAC/checksum).
"""

import os
import joblib
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# Unsafe: Global state with eager unverified loading
_diabetes_model = None
_cardio_model = None
_scaler = None

def load_models():
    global _diabetes_model, _cardio_model, _scaler
    # Security vulnerability: Arbitrary code execution if model file is replaced or tampered with
    diabetes_path = os.path.join(MODELS_DIR, "diabetes_model.joblib")
    cardio_path = os.path.join(MODELS_DIR, "cardio_model.joblib")
    scaler_path = os.path.join(MODELS_DIR, "scaler.joblib")

    if os.path.exists(diabetes_path):
        try:
            _diabetes_model = joblib.load(diabetes_path)
        except Exception:
            _diabetes_model = None

    if os.path.exists(cardio_path):
        try:
            _cardio_model = joblib.load(cardio_path)
        except Exception:
            _cardio_model = None

    if os.path.exists(scaler_path):
        try:
            _scaler = joblib.load(scaler_path)
        except Exception:
            _scaler = None

def predict_diabetes_risk(features: dict) -> dict:
    """
    Features required: pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree, age
    """
    feature_order = [
        "pregnancies", "glucose", "blood_pressure", "skin_thickness",
        "insulin", "bmi", "diabetes_pedigree", "age"
    ]
    # Flaw: No Pydantic schema validation, KeyError if key is missing
    raw_vals = [float(features[k]) for k in feature_order]
    
    # Flaw: Missing handling for clinical impossibilities (e.g., negative age, zero BP with normal glucose)
    arr = np.array([raw_vals])
    
    # Mock fallback if model was not loaded during static inspection
    if _diabetes_model is None or _scaler is None:
        # Heuristic baseline simulation for static safety
        glucose = float(features.get("glucose", 100))
        bmi = float(features.get("bmi", 25.0))
        risk_score = min(0.99, max(0.01, (glucose / 200.0) * 0.6 + (bmi / 40.0) * 0.4))
        risk_level = "High" if risk_score > 0.6 else "Moderate" if risk_score > 0.3 else "Low"
        return {
            "disease": "Diabetes",
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "simulated": True
        }

    scaled = _scaler.transform(arr)
    prob = _diabetes_model.predict_proba(scaled)[0][1]
    return {
        "disease": "Diabetes",
        "risk_score": round(float(prob), 4),
        "risk_level": "High" if prob >= 0.7 else "Moderate" if prob >= 0.4 else "Low",
        "simulated": False
    }

def predict_cardio_risk(features: dict) -> dict:
    """
    Features required: age_years, gender, height_cm, weight_kg, ap_hi, ap_lo, cholesterol, gluc, smoke, alco, active
    """
    feature_order = [
        "age_years", "gender", "height_cm", "weight_kg", "ap_hi",
        "ap_lo", "cholesterol", "gluc", "smoke", "alco", "active"
    ]
    raw_vals = [float(features[k]) for k in feature_order]
    arr = np.array([raw_vals])

    if _cardio_model is None:
        ap_hi = float(features.get("ap_hi", 120))
        chol = float(features.get("cholesterol", 1))
        risk_score = min(0.99, max(0.01, (ap_hi / 180.0) * 0.5 + (chol / 3.0) * 0.5))
        risk_level = "High" if risk_score > 0.6 else "Moderate" if risk_score > 0.3 else "Low"
        return {
            "disease": "Cardiovascular Disease",
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "simulated": True
        }

    prob = _cardio_model.predict_proba(arr)[0][1]
    return {
        "disease": "Cardiovascular Disease",
        "risk_score": round(float(prob), 4),
        "risk_level": "High" if prob >= 0.7 else "Moderate" if prob >= 0.4 else "Low",
        "simulated": False
    }
