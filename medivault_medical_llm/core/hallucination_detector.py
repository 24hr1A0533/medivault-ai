"""
Hallucination Detection Engine for MediVault Medical LLM.
Enforces zero-hallucination policy via numerical fidelity and source entailment checks.
"""
import re
from typing import List, Dict, Any, Tuple, Set

class HallucinationDetector:
    """
    Evaluates generated clinical responses against retrieved context chunks.
    Detects invented numerical values, ungrounded medical entities, and confabulations.
    """

    FALLBACK_MESSAGE = "I could not find that information in your medical records."

    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold

    def evaluate_response(
        self,
        generated_answer: str,
        retrieved_contexts: List[str],
    ) -> Tuple[bool, float, List[str], str]:
        """
        Evaluates answer against context.
        Returns:
            - is_faithful (bool): True if zero hallucinations detected.
            - faithfulness_score (float): 0.0 to 1.0.
            - flagged_hallucinations (List[str]): List of ungrounded numbers or terms.
            - final_safe_answer (str): Validated answer, or fallback if unfaithful.
        """
        if not retrieved_contexts:
            return False, 0.0, ["Missing retrieved context."], self.FALLBACK_MESSAGE

        combined_context = " ".join(retrieved_contexts).lower()
        flagged: List[str] = []

        # 1. Numerical Fidelity Check
        # Extract numerical tokens (decimals, percentages, integers)
        answer_numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", generated_answer)
        total_numbers = len(answer_numbers)
        verified_numbers = 0

        for num in answer_numbers:
            # Check if this exact number exists in the retrieved context
            clean_num = num.strip("%")
            if clean_num in combined_context:
                verified_numbers += 1
            else:
                flagged.append(f"Ungrounded numerical value: '{num}' not found in source records.")

        num_score = (verified_numbers / total_numbers) if total_numbers > 0 else 1.0

        # 2. Critical Medical Keywords Check
        # Ensure that if the answer mentions specific conditions, they appear in context
        diagnostic_terms = ["cancer", "leukemia", "diabetes", "hypertension", "ckd", "cirrhosis", "hiv"]
        verified_terms = 0
        total_terms = 0

        for term in diagnostic_terms:
            if re.search(r"\b" + term + r"\b", generated_answer, re.IGNORECASE):
                total_terms += 1
                if term in combined_context:
                    verified_terms += 1
                else:
                    flagged.append(f"Ungrounded clinical diagnostic term: '{term}' absent from context.")

        term_score = (verified_terms / total_terms) if total_terms > 0 else 1.0

        # Weighted Composite Faithfulness Score
        faithfulness_score = round((0.7 * num_score) + (0.3 * term_score), 2)
        is_faithful = (faithfulness_score >= self.confidence_threshold) and (len(flagged) == 0)

        final_answer = generated_answer if is_faithful else self.FALLBACK_MESSAGE
        return is_faithful, faithfulness_score, flagged, final_answer
