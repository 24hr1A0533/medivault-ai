# Medical Trend Analysis Engine Architecture Specification

## 1. Executive Summary & Clinical Objectives

Longitudinal monitoring of lab biomarkers is essential for managing chronic diseases (diabetes, hypertension, chronic kidney disease, dyslipidemia). The **MediVault Medical Trend Analysis Engine** ingests chronological patient reports, normalizes lab biomarkers, analyzes historical trajectory, detects improvement/deterioration, and generates doctor-ready summaries with strict source attribution.

### Core Non-Negotiable Tenets:
1. **Actual Data Only**: Every value plotted or evaluated originates strictly from an authentic patient report with exact metadata (`report_name`, `page_number`, `report_date`).
2. **Never Invent Values**: Zero interpolation, synthetic fill, or halluncinated measurements. If a data point is missing, the system records `INSUFFICIENT_DATA`.
3. **Mandatory Source Grounding**: Every trend conclusion, alert, and summary must cite its primary source reports.
4. **Directional Clinical Logic**: Correctly identifies whether higher or lower values represent improvement or deterioration based on biomarker physiology (e.g., HbA1c decrease = improvement; eGFR decrease = deterioration).

---

## 2. System Architecture

```
Patient Historical Reports (PDF, Text, Structured JSON)
                            │
                            ▼
               [Clinical Biomarker Extractor]
      (Extracts Test Name, Value, Unit, Reference Range, Date, Page)
                            │
                            ▼
              [Temporal Alignment & Normalizer]
      (Standardizes units: mg/dL, mmol/L, %; sorts chronologically)
                            │
                            ▼
                [Biomarker Trajectory Engine]
      (Calculates absolute delta, % change, slope, variance)
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 [Improvement]       [Deterioration]       [Trend Graph]
   Summary               Alerts              Generator
   Engine                Engine            (SVG + JSON)
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
              [Doctor-Ready Summary Builder]
                            │
                            ▼
          [Grounding & Citation Verification]
                            │
                            ▼
        Output: Summary, Explanation, Confidence, Citations
```

---

## 3. Supported Clinical Biomarkers & Directionality

| Biomarker | Standard Unit | Normal Reference | Favorable Direction | Deterioration Trigger |
|---|---|---|---|---|
| **HbA1c** | `%` | `4.0 - 5.6%` | Lower (towards normal) | Increase $\ge 0.5\%$ or $> 7.0\%$ |
| **Fasting Blood Glucose** | `mg/dL` | `70 - 99 mg/dL` | Lower (towards normal) | Increase $\ge 20$ mg/dL or $> 126$ mg/dL |
| **Serum Creatinine** | `mg/dL` | `0.7 - 1.3 mg/dL` | Lower (towards normal) | Increase $\ge 0.3$ mg/dL or $> 1.4$ mg/dL |
| **eGFR** | `mL/min/1.73m²` | `> 90` | Higher | Drop $\ge 10$ mL/min or $< 60$ |
| **Total Cholesterol** | `mg/dL` | `< 200 mg/dL` | Lower | Increase $\ge 20$ mg/dL or $> 240$ mg/dL |
| **LDL Cholesterol** | `mg/dL` | `< 100 mg/dL` | Lower | Increase $\ge 15$ mg/dL or $> 130$ mg/dL |
| **HDL Cholesterol** | `mg/dL` | `> 40 (M) / > 50 (F)` | Higher | Drop $< 40$ mg/dL |
| **Triglycerides** | `mg/dL` | `< 150 mg/dL` | Lower | Increase $\ge 30$ mg/dL or $> 200$ mg/dL |
| **Systolic BP** | `mmHg` | `90 - 120 mmHg` | Towards normal | Increase $> 140$ mmHg or delta $> 15$ mmHg |
| **Diastolic BP** | `mmHg` | `60 - 80 mmHg` | Towards normal | Increase $> 90$ mmHg or delta $> 10$ mmHg |
