"""
Training script for Disease Prediction Models.
WARNING: Contains multiple data science and clinical validation flaws.
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def train_diabetes():
    print("Training diabetes model...")
    df = pd.read_csv("data/diabetes_subset.csv")
    X = df.drop(columns=["outcome"])
    y = df["outcome"]

    # Flaw: No stratify=y on train_test_split despite imbalanced class distribution
    # Flaw: Imputation missing for zero-values representing missing data (e.g., BloodPressure=0, BMI=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    # Flaw: Scaling fit on whole dataset or inconsistent pipeline encapsulation
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Flaw: Overfitting without regularisation or hyperparameter tuning
    clf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=42)
    clf.fit(X_train_scaled, y_train)

    preds = clf.predict(X_test_scaled)
    acc = accuracy_score(y_test, preds)
    print(f"Diabetes Model Test Accuracy: {acc:.4f}")

    joblib.dump(clf, "models/diabetes_model.joblib")
    joblib.dump(scaler, "models/scaler.joblib")

def train_cardio():
    print("Training cardio model...")
    df = pd.read_csv("data/cardio_subset.csv")
    X = df.drop(columns=["cardio"])
    y = df["cardio"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = GradientBoostingClassifier(random_state=42)
    clf.fit(X_train, y_train)

    joblib.dump(clf, "models/cardio_model.joblib")

if __name__ == "__main__":
    train_diabetes()
    train_cardio()
