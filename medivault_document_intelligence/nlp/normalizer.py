"""
Medical Terminology Normalizer
Normalizes extracted clinical entities into standardized ontologies:
- LOINC codes for laboratory tests
- RxNorm Concept Unique Identifiers (RxCUI) for pharmaceuticals
- Standardized blood groups (ABO + Rh)
- Prescription frequency codes and durations
"""

import re
from typing import Dict, Optional, Tuple, Any


class MedicalNormalizer:
    """
    Encapsulates clinical terminology mapping across LOINC, RxNorm, UCUM, and Latin Rx notation.
    """

    # Comprehensive LOINC mapping for common clinical lab tests
    LOINC_MAP = {
        "hemoglobin": {"code": "718-7", "display": "Hemoglobin [Mass/volume] in Blood", "unit": "g/dL"},
        "glucose": {"code": "1558-6", "display": "Fasting Glucose [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "fasting blood sugar": {"code": "1558-6", "display": "Fasting Glucose [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "fbs": {"code": "1558-6", "display": "Fasting Glucose [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "postprandial blood sugar": {"code": "1521-4", "display": "Glucose 2 hours post meal in Serum or Plasma", "unit": "mg/dL"},
        "ppbs": {"code": "1521-4", "display": "Glucose 2 hours post meal in Serum or Plasma", "unit": "mg/dL"},
        "hba1c": {"code": "4548-4", "display": "Hemoglobin A1c/Hemoglobin.total in Blood", "unit": "%"},
        "creatinine": {"code": "2160-0", "display": "Creatinine [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "serum creatinine": {"code": "2160-0", "display": "Creatinine [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "blood urea nitrogen": {"code": "3094-0", "display": "Urea nitrogen [Mass/volume] in Blood", "unit": "mg/dL"},
        "bun": {"code": "3094-0", "display": "Urea nitrogen [Mass/volume] in Blood", "unit": "mg/dL"},
        "urea": {"code": "3094-0", "display": "Urea nitrogen [Mass/volume] in Blood", "unit": "mg/dL"},
        "cholesterol": {"code": "2093-3", "display": "Cholesterol [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "total cholesterol": {"code": "2093-3", "display": "Cholesterol [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "triglycerides": {"code": "2571-8", "display": "Triglyceride [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "hdl cholesterol": {"code": "2085-9", "display": "Cholesterol in HDL [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "hdl": {"code": "2085-9", "display": "Cholesterol in HDL [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "ldl cholesterol": {"code": "2089-1", "display": "Cholesterol in LDL [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "ldl": {"code": "2089-1", "display": "Cholesterol in LDL [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "platelet": {"code": "777-3", "display": "Platelets [#/volume] in Blood", "unit": "10^3/uL"},
        "platelet count": {"code": "777-3", "display": "Platelets [#/volume] in Blood", "unit": "10^3/uL"},
        "wbc": {"code": "6690-2", "display": "Leukocytes [#/volume] in Blood", "unit": "10^3/uL"},
        "white blood cells": {"code": "6690-2", "display": "Leukocytes [#/volume] in Blood", "unit": "10^3/uL"},
        "rbc": {"code": "789-8", "display": "Erythrocytes [#/volume] in Blood", "unit": "10^6/uL"},
        "red blood cells": {"code": "789-8", "display": "Erythrocytes [#/volume] in Blood", "unit": "10^6/uL"},
        "tsh": {"code": "3016-3", "display": "Thyrotropin [Units/volume] in Serum or Plasma", "unit": "uIU/mL"},
        "thyroid stimulating hormone": {"code": "3016-3", "display": "Thyrotropin [Units/volume] in Serum or Plasma", "unit": "uIU/mL"},
        "bilirubin": {"code": "1975-2", "display": "Bilirubin.total [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
        "potassium": {"code": "2823-3", "display": "Potassium [Moles/volume] in Serum or Plasma", "unit": "mmol/L"},
        "sodium": {"code": "2951-2", "display": "Sodium [Moles/volume] in Serum or Plasma", "unit": "mmol/L"},
        "calcium": {"code": "17861-6", "display": "Calcium [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
    }

    # Common pharmaceutical drugs mapped to RxNorm Concept Unique Identifiers (RxCUI)
    RXNORM_MAP = {
        "metformin": {"rxcui": "6809", "name": "Metformin Hydrochloride"},
        "glucophage": {"rxcui": "105029", "name": "Glucophage (Metformin)"},
        "amoxicillin": {"rxcui": "723", "name": "Amoxicillin"},
        "augmentin": {"rxcui": "215682", "name": "Augmentin (Amoxicillin/Clavulanate)"},
        "atorvastatin": {"rxcui": "83367", "name": "Atorvastatin Calcium"},
        "lipitor": {"rxcui": "153666", "name": "Lipitor (Atorvastatin)"},
        "paracetamol": {"rxcui": "161", "name": "Acetaminophen / Paracetamol"},
        "acetaminophen": {"rxcui": "161", "name": "Acetaminophen"},
        "tylenol": {"rxcui": "202433", "name": "Tylenol (Acetaminophen)"},
        "lisinopril": {"rxcui": "29046", "name": "Lisinopril"},
        "prinivil": {"rxcui": "202450", "name": "Prinivil (Lisinopril)"},
        "levothyroxine": {"rxcui": "6377", "name": "Levothyroxine Sodium"},
        "synthroid": {"rxcui": "220592", "name": "Synthroid (Levothyroxine)"},
        "amlodipine": {"rxcui": "17767", "name": "Amlodipine Besylate"},
        "norvasc": {"rxcui": "202476", "name": "Norvasc (Amlodipine)"},
        "losartan": {"rxcui": "5224", "name": "Losartan Potassium"},
        "cozaar": {"rxcui": "202484", "name": "Cozaar (Losartan)"},
        "omeprazole": {"rxcui": "7646", "name": "Omeprazole"},
        "prilosec": {"rxcui": "153744", "name": "Prilosec (Omeprazole)"},
        "pantoprazole": {"rxcui": "40790", "name": "Pantoprazole Sodium"},
        "protonix": {"rxcui": "220641", "name": "Protonix (Pantoprazole)"},
        "azithromycin": {"rxcui": "18631", "name": "Azithromycin"},
        "zithromax": {"rxcui": "202492", "name": "Zithromax (Azithromycin)"},
        "ciprofloxacin": {"rxcui": "2551", "name": "Ciprofloxacin Hydrochloride"},
        "cipro": {"rxcui": "202500", "name": "Cipro (Ciprofloxacin)"},
        "ibuprofen": {"rxcui": "5640", "name": "Ibuprofen"},
        "advil": {"rxcui": "153716", "name": "Advil (Ibuprofen)"},
        "aspirin": {"rxcui": "1191", "name": "Aspirin"},
        "insulin": {"rxcui": "5856", "name": "Insulin Human"},
        "hydrochlorothiazide": {"rxcui": "5487", "name": "Hydrochlorothiazide"},
        "gabapentin": {"rxcui": "25480", "name": "Gabapentin"},
        "sertraline": {"rxcui": "36437", "name": "Sertraline Hydrochloride"},
        "zoloft": {"rxcui": "202518", "name": "Zoloft (Sertraline)"},
        "metoprolol": {"rxcui": "6918", "name": "Metoprolol Tartrate"},
    }

    # Latin Sig / Medical frequency abbreviations
    FREQUENCY_MAP = {
        "od": "Once daily (every 24 hours)",
        "qd": "Once daily (every 24 hours)",
        "once daily": "Once daily (every 24 hours)",
        "bd": "Twice daily (every 12 hours)",
        "bid": "Twice daily (every 12 hours)",
        "twice daily": "Twice daily (every 12 hours)",
        "tid": "Three times daily (every 8 hours)",
        "tds": "Three times daily (every 8 hours)",
        "three times daily": "Three times daily (every 8 hours)",
        "qid": "Four times daily (every 6 hours)",
        "qds": "Four times daily (every 6 hours)",
        "four times daily": "Four times daily (every 6 hours)",
        "prn": "As needed (pro re nata)",
        "sos": "As needed (in emergency)",
        "hs": "At bedtime (hora somni)",
        "q8h": "Every 8 hours",
        "q12h": "Every 12 hours",
        "stat": "Immediately (statim)",
    }

    # Valid ABO and Rh blood group permutations
    VALID_BLOOD_GROUPS = {"a+", "a-", "b+", "b-", "ab+", "ab-", "o+", "o-"}

    def normalize_test_name(self, test_name: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Normalizes a test name.
        Returns:
            Tuple[standardized_name, loinc_code, standard_unit]
        """
        clean = test_name.strip().lower()
        # Direct lookup
        if clean in self.LOINC_MAP:
            info = self.LOINC_MAP[clean]
            return clean.title(), info["code"], info["unit"]

        # Substring lookup
        for key, info in self.LOINC_MAP.items():
            if key in clean or clean in key:
                return key.title(), info["code"], info["unit"]

        return test_name.title(), None, None

    def normalize_medicine(self, medicine_name: str) -> Tuple[str, Optional[str]]:
        """
        Normalizes medication name to active generic ingredient and RxCUI code.
        Returns:
            Tuple[standardized_name, rxcui_code]
        """
        clean = medicine_name.strip().lower()
        # Remove trailing dosage if part of name string (e.g. "Metformin 500mg" -> "Metformin")
        base_name = re.sub(r"\b\d+(\.\d+)?\s*(mg|ml|mcg|g)\b", "", clean).strip()

        if base_name in self.RXNORM_MAP:
            return self.RXNORM_MAP[base_name]["name"], self.RXNORM_MAP[base_name]["rxcui"]

        for key, info in self.RXNORM_MAP.items():
            if key in base_name or base_name in key:
                return info["name"], info["rxcui"]

        return medicine_name.title(), None

    def normalize_frequency(self, freq_str: Optional[str]) -> Optional[str]:
        """Normalizes prescription frequency string to standard expanded notation."""
        if not freq_str:
            return None
        clean = re.sub(r"[.\s]", "", freq_str.strip().lower())
        if clean in self.FREQUENCY_MAP:
            return self.FREQUENCY_MAP[clean]
        raw_clean = freq_str.strip().lower()
        if raw_clean in self.FREQUENCY_MAP:
            return self.FREQUENCY_MAP[raw_clean]
        return freq_str.strip()

    def normalize_blood_group(self, blood_str: Optional[str]) -> Optional[str]:
        """Validates and formats ABO and Rh blood group."""
        if not blood_str:
            return None
        clean = blood_str.strip().upper().replace("POSITIVE", "+").replace("NEGATIVE", "-").replace(" ", "")
        if clean.lower() in self.VALID_BLOOD_GROUPS:
            return clean
        return None

    def normalize_unit(self, unit_str: Optional[str]) -> Optional[str]:
        """Converts unit string to UCUM clinical standard."""
        if not unit_str:
            return None
        clean = unit_str.strip().lower()
        replacements = {
            "mg/dl": "mg/dL",
            "mg/100ml": "mg/dL",
            "g/dl": "g/dL",
            "gm/dl": "g/dL",
            "mmol/l": "mmol/L",
            "iu/l": "IU/L",
            "u/l": "U/L",
            "ug/dl": "mcg/dL",
            "mcg/dl": "mcg/dL",
            "%": "%",
            "10^3/ul": "10^3/uL",
            "/cumm": "/mcL",
        }
        return replacements.get(clean, unit_str.strip())
