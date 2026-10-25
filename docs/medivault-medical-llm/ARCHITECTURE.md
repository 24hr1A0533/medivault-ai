# MediVault Medical LLM Architecture Specification

## 1. Executive Summary & System Blueprint

The **MediVault Medical LLM** is an enterprise-scale clinical intelligence platform built specifically for healthcare networks, telemedicine providers, and smart health vaults.

It integrates 10 foundational capabilities into a unified, HIPAA-inspired, defense-in-depth architecture powered by **Qwen 2.5 7B**, **BGE Large Embeddings**, **ChromaDB Vector Storage**, and **vLLM Continuous Batching Inference**:

```
                       Scanned Documents / Digital Reports / PDFs
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ 1. Medical OCR & Layout Understanding Engine │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ 2. Medical Entity Extraction & Structuring   │
                    │    (Biomarkers, Values, Units, Drugs, Dates) │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ 10. Multi-User Cryptographic Tenant Isolation│
                    │  - BAAI BGE Large Dense Embedding (1024-dim) │
                    │  - ChromaDB Isolated Collections & Filtering │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
  User Query ──► [7. Safety Guardrails] ──► [3. Patient-Specific RAG Retriever]
  (Shields injection,                      (Metadata filtered: where={"patient_id": id})
   blocks diagnostic liability)                            │
                                                           ▼
                                           ┌───────────────────────────────┐
                                           │ Context Builder & Synthesizer │
                                           └───────────────┬───────────────┘
                                                           │
                                                           ▼
                                           ┌───────────────────────────────┐
                                           │ Qwen 2.5 7B via vLLM Server   │
                                           │ (4. Report Explanation)       │
                                           │ (5. Trend Analysis)           │
                                           │ (6. Doctor Summary Generation)│
                                           └───────────────┬───────────────┘
                                                           │
                                                           ▼
                                           ┌───────────────────────────────┐
                                           │ 9. Hallucination Detection    │
                                           │    (NLI & Numerical Fidelity) │
                                           └───────────────┬───────────────┘
                                                           │
                                                           ▼
                                           ┌───────────────────────────────┐
                                           │ 8. Citation & Grounding Engine│
                                           │ [Report Name, Page #, Date]   │
                                           └───────────────┬───────────────┘
                                                           │
                                                           ▼
                                               Verified Clinical Answer
```

---

## 2. The 10 Core Capabilities Matrix

| # | Capability | Technology / Architecture | Guarantee |
|---|---|---|---|
| **1** | **Medical OCR Understanding** | Layout-aware OCR parsing text, bounding boxes, and lab test tables. | Extracts raw text while preserving page numbers and table structure. |
| **2** | **Medical Knowledge Extraction** | Regex & clinical entity extractor for biomarkers, units, reference intervals, prescriptions. | Normalizes names and formats into canonical schema. |
| **3** | **Patient-Specific RAG** | BAAI BGE Large (`1024-dim`) embeddings + isolated ChromaDB semantic retrieval. | Only documents belonging to the querying patient are retrieved. |
| **4** | **Medical Report Explanation** | Qwen 2.5 7B reasoning engine with prompt grounding. | Translates complex clinical reports into educational patient language. |
| **5** | **Medical Trend Analysis** | Longitudinal trajectory calculator (delta %, slope, normal range convergence). | Cites historical values (e.g. HbA1c Jan=8.5, Apr=7.1, Jul=6.3); alerts on deterioration. |
| **6** | **Doctor Summary Generation** | Structured briefing note synthesizer. | Generates Patient Summary, Abnormal Findings, Recent Reports, Current Medications, and Questions for the Doctor. |
| **7** | **Medical Safety Guardrails** | Multi-tier Prompt Shield, Risk Classifier, and Output Filter. | Prohibits diagnostic claims, prescriptions, and dosage adjustments. |
| **8** | **Citation Engine** | Source attribution verification engine. | Every clinical statement cites `[Report Name, Page Number, Report Date]`. |
| **9** | **Hallucination Detection** | Numerical fidelity validator and claim-to-context entailment engine. | Detects ungrounded assertions; enforces zero hallucination policy. |
| **10** | **Multi-User Isolation** | Three-tier isolation: API validation, ChromaDB metadata partition, post-retrieval assertion. | Mathematical guarantee: zero cross-patient data leakage. |

---

## 3. Technology Stack Specification

- **Foundational LLM**: `Qwen/Qwen2.5-7B-Instruct` (128k context support, medical reasoning, structured ChatML output).
- **Embedding Model**: `BAAI/bge-large-en-v1.5` (1024-dimensional normalized dense vectors, leading MTEB retrieval benchmark).
- **Vector Database**: `ChromaDB` (Persistent tenant partitioning with Cosine / HNSW index).
- **Inference Runtime**: `vLLM` (Continuous Batching, PagedAttention, KV-cache optimization, tensor parallelism).
- **Security & Compliance**: HIPAA-inspired PHI de-identification, SHA-256 audit hashing, tenant-isolated vector namespaces.
