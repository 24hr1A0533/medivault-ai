"""
Medical OCR Error Correction Engine
Uses SymSpell algorithm and a curated clinical lexicon (UMLS, RxNorm, LOINC)
to correct optical character misrecognitions in medical terms.
"""

import re
from typing import Dict, List, Optional, Tuple


class MedicalSpellCorrector:
    """
    High-speed symmetric delete spelling corrector tailored for clinical vocabularies.
    Fixes typical digit-for-letter substitutions (e.g. '0' for 'O', '1' for 'l' or 'I'),
    scanner noise, and typographical omissions.
    """

    # Common OCR character confusions in medical contexts
    OCR_SUBSTITUTIONS = [
        (r"\b0(?=[A-Za-z])", "O"),
        (r"(?<=[A-Za-z])0\b", "o"),
        (r"(?<=[A-Za-z])1(?=[A-Za-z])", "l"),
        (r"\b5(?=[A-Za-z])", "S"),
        (r"(?<=[A-Za-z])5\b", "s"),
        (r"\b8(?=[A-Za-z])", "B"),
    ]

    # Curated clinical lexicon of frequent medical test names, drugs, and units
    CLINICAL_LEXICON = {
        # Lab tests
        "hemoglobin": 1000,
        "glucose": 1000,
        "creatinine": 950,
        "platelet": 900,
        "cholesterol": 900,
        "triglycerides": 850,
        "bilirubin": 850,
        "potassium": 800,
        "sodium": 800,
        "calcium": 800,
        "albumin": 750,
        "leukocytes": 750,
        "erythrocytes": 700,
        "hematocrit": 700,
        "neutrophils": 650,
        "lymphocytes": 650,
        "eosinophils": 600,
        "monocytes": 600,
        "basophils": 550,
        "urea": 800,
        "protein": 800,
        "uric acid": 750,
        "thyroid": 700,
        "tsh": 900,
        "hba1c": 950,
        # Medications
        "metformin": 1000,
        "amoxicillin": 950,
        "atorvastatin": 950,
        "paracetamol": 900,
        "acetaminophen": 900,
        "lisinopril": 850,
        "levothyroxine": 850,
        "amlodipine": 800,
        "losartan": 800,
        "omeprazole": 800,
        "pantoprazole": 800,
        "azithromycin": 750,
        "ciprofloxacin": 750,
        "ibuprofen": 750,
        "aspirin": 850,
        "insulin": 900,
        "hydrochlorothiazide": 700,
        "gabapentin": 700,
        "sertraline": 650,
        "metoprolol": 650,
        # Units
        "mg/dl": 1000,
        "g/dl": 950,
        "mmol/l": 900,
        "iu/l": 850,
        "ug/dl": 800,
        "fl": 750,
        "pg": 750,
    }

    # Explicit mapping for common severe OCR distortions
    KNOWN_CORRECTIONS = {
        "gluc0se": "glucose",
        "hem0globin": "hemoglobin",
        "haemoglobin": "hemoglobin",
        "hgb": "hemoglobin",
        "creat1n1ne": "creatinine",
        "creatinin": "creatinine",
        "platlets": "platelet",
        "platelets": "platelet",
        "cholestrol": "cholesterol",
        "triglycerid": "triglycerides",
        "metfornnin": "metformin",
        "metformn": "metformin",
        "amoxcillin": "amoxicillin",
        "atorvastatn": "atorvastatin",
        "paracetemol": "paracetamol",
        "omeprazol": "omeprazole",
        "azithromyc1n": "azithromycin",
        "hbaic": "hba1c",
        "hb-a1c": "hba1c",
    }

    def __init__(self):
        self._deletes: Dict[str, List[str]] = {}
        self._build_delete_dictionary()

    def _build_delete_dictionary(self):
        """Constructs symmetric deletion hash index (edit distance <= 1)."""
        for word in self.CLINICAL_LEXICON:
            self._add_to_dict(word)

    def _add_to_dict(self, word: str):
        deletes = self._get_deletes(word)
        for item in deletes:
            if item not in self._deletes:
                self._deletes[item] = []
            if word not in self._deletes[item]:
                self._deletes[item].append(word)

    def _get_deletes(self, word: str) -> List[str]:
        deletes = []
        for i in range(len(word)):
            deletes.append(word[:i] + word[i + 1:])
        return deletes

    def clean_ocr_artefacts(self, text: str) -> str:
        """Applies regex rules to fix obvious digit-letter OCR blendings."""
        result = text
        for pattern, replacement in self.OCR_SUBSTITUTIONS:
            result = re.sub(pattern, replacement, result)
        return result

    def correct_term(self, term: str) -> Tuple[str, float]:
        """
        Corrects a clinical term.
        Returns:
            Tuple[corrected_term, correction_confidence]
        """
        clean = term.strip().lower()
        if not clean:
            return term, 1.0

        # Direct hit in lexicon
        if clean in self.CLINICAL_LEXICON:
            return clean, 1.0

        # Known manual mapping
        if clean in self.KNOWN_CORRECTIONS:
            return self.KNOWN_CORRECTIONS[clean], 0.95

        # Check deletion index
        candidates = []
        if clean in self._deletes:
            candidates.extend(self._deletes[clean])

        deletes = self._get_deletes(clean)
        for item in deletes:
            if item in self._deletes:
                candidates.extend(self._deletes[item])

        if candidates:
            # Score candidates by frequency and Levenshtein similarity
            scored = []
            for cand in set(candidates):
                sim = self._levenshtein_similarity(clean, cand)
                freq = self.CLINICAL_LEXICON.get(cand, 100)
                scored.append((cand, sim, freq))

            scored.sort(key=lambda x: (x[1], x[2]), reverse=True)
            best_cand, best_sim, _ = scored[0]
            if best_sim >= 0.75:
                return best_cand, round(best_sim, 2)

        return term, 0.80

    def correct_text_block(self, text: str) -> str:
        """Performs token-by-token clinical correction across a multi-line text block."""
        cleaned = self.clean_ocr_artefacts(text)
        words = re.split(r"(\s+|,|:)", cleaned)
        corrected_words = []
        for w in words:
            if re.match(r"^[A-Za-z0-9_-]{3,}$", w):
                corrected, _ = self.correct_term(w)
                corrected_words.append(corrected)
            else:
                corrected_words.append(w)
        return "".join(corrected_words)

    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Computes normalized Levenshtein similarity in [0, 1]."""
        m, n = len(s1), len(s2)
        if m == 0 or n == 0:
            return 0.0
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
        dist = dp[m][n]
        max_len = max(m, n)
        return 1.0 - (dist / max_len)
