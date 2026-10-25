"""
Test suite for Healthcare LLM Engineering Pipeline.

Verifies:
- Model and QLoRA configuration parameters
- Dataset pipeline transformations for MIMIC-IV, PubMedQA, MedQA, and MedMCQA
- ChatML formatting and sequence preparation
- vLLM Inference Server REST endpoints
- Client async integration
"""
import pytest
from fastapi.testclient import TestClient

from medivault_healthcare_llm.config.training_config import (
    ModelConfig,
    QLoRAConfig,
    QuantizationConfig,
    TrainingHyperparameters,
)
from medivault_healthcare_llm.dataset.data_schema import (
    MedicalTaskType,
    ChatMessage,
    MedicalTrainingSample,
)
from medivault_healthcare_llm.dataset.dataset_pipeline import HealthcareDatasetPipeline
from medivault_healthcare_llm.inference.vllm_engine import app

@pytest.fixture
def dataset_pipeline():
    return HealthcareDatasetPipeline()

@pytest.fixture
def client():
    return TestClient(app)


def test_qlora_and_quantization_configs():
    """
    Verify QLoRA hyperparameters:
    - 4-bit NormalFloat (NF4)
    - Double Quantization enabled
    - Rank = 64, Alpha = 128
    - All 7 linear target projections included
    """
    m_cfg = ModelConfig()
    assert "Qwen2.5-7B" in m_cfg.base_model_name_or_path
    assert m_cfg.model_max_length >= 4096

    qlora_cfg = QLoRAConfig()
    assert qlora_cfg.r == 64
    assert qlora_cfg.lora_alpha == 128
    assert len(qlora_cfg.target_modules) == 7
    assert "q_proj" in qlora_cfg.target_modules
    assert "down_proj" in qlora_cfg.target_modules

    quant_cfg = QuantizationConfig()
    assert quant_cfg.load_in_4bit is True
    assert quant_cfg.bnb_4bit_quant_type == "nf4"
    assert quant_cfg.bnb_4bit_use_double_quant is True
    assert quant_cfg.bnb_4bit_compute_dtype == "bfloat16"


def test_mimic_iv_report_explanation_transformation(dataset_pipeline):
    """
    Verify transformation of MIMIC-IV clinical discharge summary into report explanation task.
    """
    sample = dataset_pipeline.transform_mimic_iv_sample(
        sample_id="10045",
        discharge_summary_text="Patient admitted for DKA. Managed on IV insulin infusion. Discharged on Metformin 500mg BID.",
        target_explanation="Hospital course focused on resolution of diabetic ketoacidosis with transition to oral antihyperglycemic therapy.",
    )

    assert sample.dataset_source == "MIMIC-IV"
    assert sample.task_type == MedicalTaskType.REPORT_EXPLANATION
    assert len(sample.messages) == 3
    assert sample.messages[0].role == "system"
    assert sample.messages[1].role == "user"
    assert sample.messages[2].role == "assistant"

    # ChatML formatting check
    chatml = sample.to_chatml()
    assert "<|im_start|>system" in chatml
    assert "<|im_start|>user" in chatml
    assert "<|im_start|>assistant" in chatml
    assert "<|im_end|>" in chatml


def test_pubmedqa_rag_answering_transformation(dataset_pipeline):
    """
    Verify transformation of PubMedQA biomedical abstract into RAG answering task.
    """
    sample = dataset_pipeline.transform_pubmedqa_sample(
        sample_id="99231",
        question="Does SGLT2 inhibition reduce cardiovascular mortality in heart failure?",
        abstract_context="Clinical trial demonstrated 25% relative risk reduction in cardiovascular death with empagliflozin.",
        answer="Yes. SGLT2 inhibitors demonstrate significant reduction in cardiovascular death and heart failure hospitalizations.",
    )

    assert sample.dataset_source == "PubMedQA"
    assert sample.task_type == MedicalTaskType.RAG_ANSWERING
    assert "EVIDENCE CONTEXT:" in sample.messages[1].content
    assert "SGLT2" in sample.messages[2].content


def test_medqa_clinical_decision_support_transformation(dataset_pipeline):
    """
    Verify transformation of MedQA USMLE vignettes into clinical reasoning pairs.
    """
    sample = dataset_pipeline.transform_medqa_sample(
        sample_id="USMLE-551",
        clinical_case_vignette="A 55-year-old male presents with exertional substernal chest pressure radiating to left arm...",
        options={
            "A": "Acute Pericarditis",
            "B": "Unstable Angina / Acute Coronary Syndrome",
            "C": "Gastroesophageal Reflux",
            "D": "Costochondritis",
        },
        correct_answer="B: Unstable Angina / Acute Coronary Syndrome",
        clinical_rationale="Exertional retrosternal pressure radiating to the arm in a middle-aged male strongly suggests myocardial ischemia.",
    )

    assert sample.dataset_source == "MedQA"
    assert sample.task_type == MedicalTaskType.CLINICAL_DECISION_SUPPORT
    assert "OPTIONS:" in sample.messages[1].content
    assert "Correct Answer: B" in sample.messages[2].content


def test_medmcqa_terminology_understanding_transformation(dataset_pipeline):
    """
    Verify transformation of MedMCQA items into medical terminology pairs.
    """
    sample = dataset_pipeline.transform_medmcqa_sample(
        sample_id="MCQA-881",
        concept_term_or_question="Mechanism of Action of Lisinopril",
        detailed_explanation="Lisinopril is an ACE inhibitor that blocks the conversion of angiotensin I to angiotensin II, decreasing peripheral vascular resistance.",
        specialty="Pharmacology",
    )

    assert sample.dataset_source == "MedMCQA"
    assert sample.task_type == MedicalTaskType.TERMINOLOGY_UNDERSTANDING
    assert sample.clinical_domain == "Pharmacology"
    assert "ACE inhibitor" in sample.messages[2].content


def test_dataset_stratified_mix_and_split(dataset_pipeline):
    """
    Verify stratified dataset mixing and 90/10 train-test splitting.
    """
    samples = []
    for i in range(100):
        samples.append(
            dataset_pipeline.transform_medmcqa_sample(
                sample_id=str(i),
                concept_term_or_question=f"Term {i}",
                detailed_explanation=f"Explanation {i}",
            )
        )

    train_set, val_set = dataset_pipeline.mix_and_split(samples, train_ratio=0.9, seed=123)
    assert len(train_set) == 90
    assert len(val_set) == 10


def test_vllm_inference_server_endpoints(client):
    """
    Test vLLM OpenAI-compatible REST server endpoints.
    """
    # 1. GET /health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"
    assert r_health.json()["gpu_available"] is True

    # 2. POST /v1/chat/completions
    payload = {
        "model": "medivault-qwen-2.5-7b",
        "messages": [
            {"role": "system", "content": "You are a clinical AI."},
            {"role": "user", "content": "Explain the significance of elevated HbA1c 8.2%."},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }

    r_chat = client.post("/v1/chat/completions", json=payload)
    assert r_chat.status_code == 200
    data = r_chat.json()
    assert data["model"] == "medivault-qwen-2.5-7b"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert len(data["choices"][0]["message"]["content"]) > 10
    assert data["usage"]["total_tokens"] > 0
