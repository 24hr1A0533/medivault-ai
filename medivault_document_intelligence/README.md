# MediVault AI — Production Healthcare Document Intelligence System

Production-grade medical document intelligence pipeline transforming unstructured medical records into validated, queryable structured knowledge.

---

## 1. System Pipeline

```
Document (PDF, JPG, PNG)
   │
   ▼
Adaptive Preprocessing (Deskewing, CLAHE, Noise Filtering)
   │
   ▼
Optical Character Recognition (PaddleOCR PP-OCRv4 Layout Analysis)
   │
   ▼
Medical OCR Error Correction (SymSpell Clinical Lexicon)
   │
   ▼
Biomedical Entity Extraction (BioBERT / ClinicalBERT)
   │
   ▼
Medical Terminology Normalization (LOINC, RxNorm, UCUM, Latin Sig)
   │
   ▼
Multimodal Confidence Scoring & Human Verification (HITL)
   │
   ▼
Dense Embeddings (BAAI BGE Large 1024-d, Instruction Formatted)
   │
   ▼
Vector Database (ChromaDB Persistent Cosine Collections)
```

---

## 2. Extracted Structured Knowledge Taxonomy

### Patient Details
- `name`: Full legal name
- `age`: Numeric age
- `gender`: Male / Female / Other
- `blood_group`: ABO + Rh ($A^+, B^+, AB^+, O^+, A^-, B^-, AB^-, O^-$)
- `confidence`: Confidence score $[0.0, 1.0]$

### Medical Lab Data
- `test_name`: Normalized laboratory parameter (e.g. `Fasting Blood Sugar`, `Hemoglobin`, `Serum Creatinine`)
- `value`: Quantitative float or qualitative finding
- `unit`: Standardized UCUM unit (`mg/dL`, `g/dL`, `mmol/L`, `%`)
- `reference_range`: Normal biological reference range (e.g. `70 - 99`)
- `is_abnormal`: Automated boolean alert for out-of-range values
- `loinc_code`: Standardized LOINC concept code (e.g. `1558-6`, `718-7`, `2160-0`)
- `report_date`: Specimen collection/report date in ISO-8601
- `hospital`: Healthcare facility / laboratory name

### Prescription Matrix
- `medicine`: Standard active generic pharmaceutical or brand name
- `dosage`: Quantity and unit strength (e.g. `500mg`, `40mg`, `10ml`)
- `frequency`: Normalized administration schedule (e.g. `Twice daily (every 12 hours)`)
- `duration`: Course duration (e.g. `30 days`, `2 weeks`)
- `rxnorm_code`: Standardized RxNorm CUI (e.g. `6809` for Metformin)

---

## 3. Technology Stack

- **OCR Engine**: PaddleOCR (PP-OCRv4 with DBNet detection & SVTR-LCNet recognition)
- **Biomedical NLP**: BioBERT (`dmis-lab/biobert-v1.1`) & ClinicalBERT (`emilyalsentzer/Bio_ClinicalBERT`)
- **Clinical Normalizers**: LOINC 2.76, RxNorm, UCUM, and Latin Sig translation
- **Embeddings**: BAAI BGE Large (`BAAI/bge-large-en-v1.5`, 1024 dimensions)
- **Vector Database**: ChromaDB (Persistent client, Cosine distance space)
- **API Framework**: FastAPI, Pydantic v2, Uvicorn

---

## 4. REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/doc-intelligence/process` | `POST` | Upload multi-page PDF or image, extract medical knowledge, generate BGE Large embeddings, and index into ChromaDB. |
| `/api/v1/doc-intelligence/documents/{doc_id}` | `GET` | Retrieve structured medical knowledge JSON. |
| `/api/v1/doc-intelligence/documents/{doc_id}/verify` | `POST` | Human-in-the-Loop review: Approve, Edit fields, or Reject structured document. |
| `/api/v1/doc-intelligence/search` | `POST` | Semantic vector search using instruction-conditioned BGE Large queries. |
| `/api/v1/doc-intelligence/health` | `GET` | Service readiness probe reporting status of OCR, NLP, Embedder, and ChromaDB. |

---

## 5. Running the Microservice

```bash
# Install dependencies
pip install -r requirements.txt

# Run pytest suite
python -m pytest medivault_document_intelligence/tests/test_document_intelligence.py -v

# Run service locally
uvicorn medivault_document_intelligence.main:app --host 0.0.0.0 --port 8001 --reload

# Run with Docker Compose
docker-compose up --build -d
```
