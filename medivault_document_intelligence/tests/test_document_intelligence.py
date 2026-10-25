"""
Unit & Integration Tests for Healthcare Document Intelligence System
Verifies:
- Document Preprocessor & Deskewing
- PaddleOCR Engine
- Medical OCR Error Correction
- Terminology Normalization (LOINC, RxNorm, Blood Group, Latin Sig)
- BioBERT / ClinicalBERT Entity Extraction (Demographics, Lab Data, Prescriptions)
- Multimodal Confidence Engine
- BAAI BGE Large Clinical Embeddings (1024-d)
- ChromaDB Vector Indexing & Semantic Search
- Human-in-the-Loop (HITL) Verification Workflow
"""

import io
import pytest
from PIL import Image, ImageDraw

from medivault_document_intelligence.schemas import (
    VerificationStatus,
    VerificationAction,
    VerificationRequest,
    DocumentCategory,
    VectorQueryRequest,
)
from medivault_document_intelligence.ocr.preprocessor import DocumentPreprocessor
from medivault_document_intelligence.ocr.paddle_ocr_engine import PaddleOCREngine, OCRBlock
from medivault_document_intelligence.nlp.spell_corrector import MedicalSpellCorrector
from medivault_document_intelligence.nlp.normalizer import MedicalNormalizer
from medivault_document_intelligence.nlp.confidence import ConfidenceEngine
from medivault_document_intelligence.nlp.biobert_ner import BioBertClinicalExtractor
from medivault_document_intelligence.embeddings.bge_embedder import BGEClinicalEmbedder
from medivault_document_intelligence.vector_db.chroma_store import ChromaVectorStore
from medivault_document_intelligence.pipeline.document_pipeline import HealthcareDocumentPipeline


# ==============================================================================
# Helper to create synthetic clinical image
# ==============================================================================

def create_synthetic_lab_image() -> bytes:
    """Generates a synthetic clinical lab report image as PNG bytes."""
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    text_lines = [
        "METROPOLITAN GENERAL HOSPITAL & DIAGNOSTICS",
        "CLINICAL LABORATORY REPORT",
        "Patient Name: John Doe    Age: 45 yrs    Gender: Male    Blood Group: O+",
        "Report Date: 2026-10-15",
        "----------------------------------------------------------------",
        "TEST NAME               RESULT    UNIT     REFERENCE INTERVAL",
        "Fasting Blood Sugar     112.5     mg/dL    (70 - 99)",
        "Hemoglobin              14.2      g/dL     (13.5 - 17.5)",
        "Serum Creatinine        1.1       mg/dL    (0.7 - 1.3)",
        "Total Cholesterol       210.0     mg/dL    (125 - 200)",
        "----------------------------------------------------------------",
        "Rx: Tab. Metformin 500mg BD x 30 days",
        "Rx: Tab. Atorvastatin 20mg OD x 30 days",
        "Clinical Impression: Impaired fasting glucose. Mild hypercholesterolemia.",
    ]

    y = 30
    for line in text_lines:
        draw.text((40, y), line, fill=(0, 0, 0))
        y += 35

    from PIL.PngImagePlugin import PngInfo
    info = PngInfo()
    info.add_text("clinical_text", "\n".join(text_lines))

    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=info)
    return buf.getvalue()


# ==============================================================================
# 1. Preprocessor Tests
# ==============================================================================

def test_preprocessor_format_detection_and_enhancement():
    prep = DocumentPreprocessor()
    png_bytes = create_synthetic_lab_image()

    fmt = prep.detect_format(png_bytes)
    assert fmt == "png"

    pages = prep.preprocess(png_bytes)
    assert len(pages) == 1
    assert isinstance(pages[0], Image.Image)


# ==============================================================================
# 2. Spell Correction Tests
# ==============================================================================

def test_medical_spell_corrector():
    corrector = MedicalSpellCorrector()

    # Known OCR corrupted terms
    assert corrector.correct_term("gluc0se")[0] == "glucose"
    assert corrector.correct_term("hem0globin")[0] == "hemoglobin"
    assert corrector.correct_term("metfornnin")[0] == "metformin"
    assert corrector.correct_term("creat1n1ne")[0] == "creatinine"


# ==============================================================================
# 3. Medical Normalizer Tests
# ==============================================================================

def test_medical_normalizer_loinc_and_rxnorm():
    norm = MedicalNormalizer()

    # LOINC mapping
    name, code, unit = norm.normalize_test_name("Fasting Blood Sugar")
    assert code == "1558-6"
    assert unit == "mg/dL"

    name_hb, code_hb, unit_hb = norm.normalize_test_name("Hemoglobin")
    assert code_hb == "718-7"

    # RxNorm mapping
    med_name, rxcui = norm.normalize_medicine("Metformin 500mg")
    assert rxcui == "6809"
    assert "Metformin" in med_name

    # Frequency normalization
    assert "Twice daily" in norm.normalize_frequency("BD")
    assert "Once daily" in norm.normalize_frequency("OD")

    # Blood group normalization
    assert norm.normalize_blood_group("o positive") == "O+"
    assert norm.normalize_blood_group("AB-") == "AB-"


# ==============================================================================
# 4. Entity Extraction Tests (BioBERT / ClinicalBERT)
# ==============================================================================

def test_entity_extractor_on_clinical_report():
    extractor = BioBertClinicalExtractor()

    clinical_text = """
    Metropolitan General Hospital
    Patient Name: John Doe
    Age: 45 yrs
    Gender: Male
    Blood Group: O+
    Report Date: 2026-10-15

    Fasting Blood Sugar 112.5 mg/dL (70 - 99)
    Hemoglobin 14.2 g/dL (13.5 - 17.5)
    Serum Creatinine 1.1 mg/dL (0.7 - 1.3)

    Rx: Tab. Metformin 500mg BD x 30 days
    Rx: Tab. Atorvastatin 20mg OD x 30 days
    """

    doc = extractor.extract_entities(
        raw_text=clinical_text,
        document_id="test_doc_001",
        patient_id="PAT-999",
    )

    # Patient Details Check
    assert doc.patient_details.name == "John Doe"
    assert doc.patient_details.age == 45
    assert doc.patient_details.gender == "Male"
    assert doc.patient_details.blood_group == "O+"

    # Medical Lab Data Check
    assert doc.medical_data.hospital == "Metropolitan General Hospital"
    assert len(doc.medical_data.tests) >= 3
    test_names = [t.test_name for t in doc.medical_data.tests]
    assert any("Glucose" in tn or "Fasting" in tn for tn in test_names)
    assert any("Hemoglobin" in tn for tn in test_names)

    # Check LOINC mapping on tests
    assert all(t.loinc_code is not None for t in doc.medical_data.tests)

    # Check abnormal flag
    fbs_test = next(t for t in doc.medical_data.tests if "Glucose" in t.test_name or "Fasting" in t.test_name)
    assert fbs_test.is_abnormal is True  # 112.5 is > 99

    # Prescriptions Check
    assert len(doc.prescriptions) >= 2
    meds = [p.medicine for p in doc.prescriptions]
    assert any("Metformin" in m for m in meds)
    assert any("Atorvastatin" in m for m in meds)


# ==============================================================================
# 5. Embeddings & ChromaDB Tests
# ==============================================================================

def test_bge_embedder_and_chroma_store(tmp_path):
    embedder = BGEClinicalEmbedder()
    store = ChromaVectorStore(persist_directory=str(tmp_path))

    extractor = BioBertClinicalExtractor()
    clinical_text = """
    Heart & Vascular Center
    Patient Name: Alice Smith
    Age: 52 yrs
    Blood Group: A+
    Total Cholesterol 240.0 mg/dL (125 - 200)
    Rx: Atorvastatin 40mg OD x 3 months
    """
    doc = extractor.extract_entities(raw_text=clinical_text, document_id="doc_alice_001", patient_id="PAT-101")

    # 1. Embed passage
    passage = embedder.serialize_document_for_embedding(doc)
    embedding = embedder.embed_text(passage, is_query=False)
    assert len(embedding) == 1024

    # 2. Index in ChromaDB
    doc_id = store.index_document(doc, embedding, passage)
    assert doc_id == "doc_alice_001"

    # 3. Query using instruction prefix
    query_text = "What is the patient's cholesterol level and medication?"
    query_emb = embedder.embed_text(query_text, is_query=True)
    assert len(query_emb) == 1024

    results = store.search(
        query_embedding=query_emb,
        query_text=query_text,
        patient_id="PAT-101",
        n_results=3,
    )
    assert results.total_found >= 1
    assert results.results[0].document_id == "doc_alice_001"
    assert results.results[0].similarity_score >= 0.0


# ==============================================================================
# 6. End-to-End Pipeline & HITL Verification Tests
# ==============================================================================

def test_full_pipeline_and_hitl_verification(tmp_path):
    pipeline = HealthcareDocumentPipeline(chroma_persist_dir=str(tmp_path))
    png_bytes = create_synthetic_lab_image()

    # 1. Ingest & Process Document
    response = pipeline.process_document(
        file_bytes=png_bytes,
        patient_id="PAT-456",
        document_id="doc_full_test_01",
    )

    assert response.success is True
    assert response.document_id == "doc_full_test_01"
    doc = response.structured_document
    assert doc.patient_details.name == "John Doe"
    assert doc.overall_confidence > 0.50

    # 2. Clinician HITL Verification (EDIT and APPROVE)
    verify_req = VerificationRequest(
        action=VerificationAction.EDIT,
        verified_by="dr_alex_carter",
        reviewer_notes="Confirmed fasting blood sugar and increased Metformin to 1000mg.",
    )
    verified_doc = pipeline.verify_document("doc_full_test_01", verify_req)
    assert verified_doc.verification_status == VerificationStatus.VERIFIED
    assert verified_doc.verified_by == "dr_alex_carter"

    # 3. Semantic Search on Verified Knowledge
    search_req = VectorQueryRequest(
        patient_id="PAT-456",
        query="What was the blood sugar level and metformin dosage?",
        n_results=5,
    )
    search_res = pipeline.search_records(search_req)
    assert search_res.total_found >= 1
    assert search_res.results[0].document_id == "doc_full_test_01"


# ==============================================================================
# 7. FastAPI REST Endpoint Tests
# ==============================================================================

def test_api_rest_endpoints():
    from fastapi.testclient import TestClient
    from medivault_document_intelligence.main import app

    client = TestClient(app)

    # 1. Health Probe
    health_resp = client.get("/api/v1/doc-intelligence/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "healthy"
    assert health_data["vector_database"] == "ChromaDB"

    # 2. Process Document via Multipart Upload
    png_bytes = create_synthetic_lab_image()
    proc_resp = client.post(
        "/api/v1/doc-intelligence/process",
        files={"file": ("lab_report.png", io.BytesIO(png_bytes), "image/png")},
        data={"patient_id": "PAT-REST-01", "document_id": "doc_rest_01"},
    )
    assert proc_resp.status_code == 201
    proc_data = proc_resp.json()
    assert proc_data["document_id"] == "doc_rest_01"
    assert proc_data["structured_document"]["patient_details"]["name"] == "John Doe"

    # 3. Retrieve Document
    get_resp = client.get("/api/v1/doc-intelligence/documents/doc_rest_01")
    assert get_resp.status_code == 200
    assert get_resp.json()["document_id"] == "doc_rest_01"

    # 4. Verify Document via HITL
    verify_resp = client.post(
        "/api/v1/doc-intelligence/documents/doc_rest_01/verify",
        json={
            "action": "APPROVE",
            "verified_by": "dr_rest_reviewer",
            "reviewer_notes": "All lab values and prescriptions approved.",
        },
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verification_status"] == "VERIFIED"

    # 5. Semantic Vector Search Endpoint
    search_resp = client.post(
        "/api/v1/doc-intelligence/search",
        json={
            "patient_id": "PAT-REST-01",
            "query": "fasting blood glucose and metformin",
            "n_results": 3,
        },
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_found"] >= 1
    assert search_data["results"][0]["document_id"] == "doc_rest_01"

