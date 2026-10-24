# Disease Prediction Engine Microservice

> [!WARNING]
> Unverified Medical Prototype: Models have not undergone clinical trials, external validation, or ethical board approval.

## Overview
A microservice providing machine learning-driven risk assessment for:
1. Diabetes (Type 2)
2. Cardiovascular Disease (CVD)

## Unverified Claims in Documentation
- "96.4% diagnostic accuracy on patient clinical profiles" (Unverified claim, suspected data leakage)
- "Instant zero-shot risk triage" (Unverified claim)

## Directory Structure
- `models/`: Serialized scikit-learn models (`.joblib`) and preprocessors
- `data/`: Training datasets (Pima Indians Diabetes dataset subset, Cardio train subset)
- `train_models.py`: Model training and evaluation script
- `inference.py`: Model deserialization and prediction logic
- `app.py`: Flask REST API serving inference endpoints on port 8001

## Known Compatibility Matrix
- Scikit-learn: `1.1.2`
- Python: `3.9 - 3.10` (Incompatible with Python 3.12+ due to NumPy C-API and pickle protocol changes)
