"""
Orchestrated Healthcare Document Intelligence Pipeline
Coordinates:
Document → OCR (PaddleOCR) → Error Correction → BioBERT NER →
Normalization (LOINC/RxNorm) → Structured JSON → Embeddings (BGE Large) → ChromaDB
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, Tuple, List

from ..schemas.document_schema import (
    StructuredMedicalDocument,
    DocumentProcessResponse,
    VerificationStatus,
    VerificationAction,
    VerificationRequest,
    VectorQueryRequest,
    VectorQueryResponse,
)
from ..ocr.preprocessor import DocumentPreprocessor
from ..ocr.paddle_ocr_engine import PaddleOCREngine
from ..nlp.biobert_ner import BioBertClinicalExtractor
from ..embeddings.bge_embedder import BGEClinicalEmbedder
from ..vector_db.chroma_store import ChromaVectorStore

logger = logging.getLogger("document_intelligence.pipeline")


class HealthcareDocumentPipeline:
    """
    Production end-to-end medical document intelligence pipeline.
    """

    def __init__(
        self,
        use_gpu: bool = False,
        chroma_persist_dir: Optional[str] = None,
    ):
        self.preprocessor = DocumentPreprocessor()
        self.ocr_engine = PaddleOCREngine(use_gpu=use_gpu)
        self.extractor = BioBertClinicalExtractor()
        self.embedder = BGEClinicalEmbedder()
        self.vector_store = ChromaVectorStore(persist_directory=chroma_persist_dir)
        # In-memory document storage registry for fast lookup and HITL review
        self._document_registry: Dict[str, StructuredMedicalDocument] = {}

    def process_document(
        self,
        file_bytes: bytes,
        patient_id: Optional[str] = None,
        document_id: Optional[str] = None,
        fallback_text: Optional[str] = None,
    ) -> DocumentProcessResponse:
        """
        Executes full pipeline:
        1. Preprocess & deskew document
        2. Execute PaddleOCR text & layout recognition
        3. Extract medical entities with BioBERT / ClinicalBERT
        4. Normalize to LOINC & RxNorm
        5. Score confidence & assign verification state
        6. Compute BAAI BGE Large embeddings
        7. Index into ChromaDB
        """
        start_time = time.time()
        doc_uuid = document_id or f"doc_{uuid.uuid4().hex[:12]}"

        # Step 1: Preprocess pages
        pages = self.preprocessor.preprocess(file_bytes)

        # Step 2: Optical Character Recognition
        full_text, ocr_blocks = self.ocr_engine.extract_full_text(pages)

        # Resilient fallback if visual OCR engine is uninstalled/unreachable
        if not full_text.strip():
            if file_bytes.startswith(b"%PDF-"):
                try:
                    import io
                    from pypdf import PdfReader
                    reader = PdfReader(io.BytesIO(file_bytes))
                    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                except Exception:
                    pass
            elif fallback_text:
                full_text = fallback_text

        # Step 3 & 4: BioBERT NER & Ontology Normalization
        structured_doc = self.extractor.extract_entities(
            raw_text=full_text,
            ocr_blocks=ocr_blocks,
            document_id=doc_uuid,
            patient_id=patient_id,
        )

        # Step 5: BAAI BGE Large Embeddings
        semantic_passage = self.embedder.serialize_document_for_embedding(structured_doc)
        embedding = self.embedder.embed_text(semantic_passage, is_query=False)

        # Step 6: ChromaDB Vector Indexing
        vector_id = self.vector_store.index_document(
            doc=structured_doc,
            embedding=embedding,
            semantic_passage=semantic_passage,
        )
        structured_doc.vector_id = vector_id

        # Persist in registry
        self._document_registry[doc_uuid] = structured_doc

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return DocumentProcessResponse(
            success=True,
            document_id=doc_uuid,
            patient_id=patient_id,
            verification_status=structured_doc.verification_status,
            overall_confidence=structured_doc.overall_confidence,
            structured_document=structured_doc,
            processing_time_ms=elapsed_ms,
            message="Document converted into structured medical knowledge and indexed in ChromaDB.",
        )

    def get_document(self, document_id: str) -> Optional[StructuredMedicalDocument]:
        """Retrieves structured document by ID."""
        return self._document_registry.get(document_id)

    def verify_document(
        self,
        document_id: str,
        request: VerificationRequest,
    ) -> StructuredMedicalDocument:
        """
        Human-in-the-Loop (HITL) verification workflow.
        Allows clinicians to approve, edit extracted fields, or reject the document.
        Re-indexes updated knowledge into ChromaDB upon verification.
        """
        doc = self._document_registry.get(document_id)
        if not doc:
            raise ValueError(f"Document '{document_id}' not found in registry.")

        from datetime import datetime, timezone

        if request.action == VerificationAction.APPROVE:
            doc.verification_status = VerificationStatus.VERIFIED
            doc.verified_at = datetime.now(timezone.utc)
            doc.verified_by = request.verified_by
            doc.reviewer_notes = request.reviewer_notes

        elif request.action == VerificationAction.EDIT:
            doc.verification_status = VerificationStatus.VERIFIED
            doc.verified_at = datetime.now(timezone.utc)
            doc.verified_by = request.verified_by
            doc.reviewer_notes = request.reviewer_notes

            # Apply clinician edits if supplied
            if request.edited_patient_details:
                doc.patient_details = request.edited_patient_details
            if request.edited_medical_data:
                doc.medical_data = request.edited_medical_data
            if request.edited_prescriptions:
                doc.prescriptions = request.edited_prescriptions

        elif request.action == VerificationAction.REJECT:
            doc.verification_status = VerificationStatus.REJECTED
            doc.verified_at = datetime.now(timezone.utc)
            doc.verified_by = request.verified_by
            doc.reviewer_notes = request.reviewer_notes

        # Re-generate embeddings and update ChromaDB
        if doc.verification_status == VerificationStatus.VERIFIED:
            semantic_passage = self.embedder.serialize_document_for_embedding(doc)
            embedding = self.embedder.embed_text(semantic_passage, is_query=False)
            self.vector_store.index_document(
                doc=doc,
                embedding=embedding,
                semantic_passage=semantic_passage,
            )

        self._document_registry[document_id] = doc
        return doc

    def search_records(self, request: VectorQueryRequest) -> VectorQueryResponse:
        """
        Executes semantic vector retrieval using query instruction prefix with BGE Large.
        """
        query_embedding = self.embedder.embed_text(request.query, is_query=True)
        return self.vector_store.search(
            query_embedding=query_embedding,
            query_text=request.query,
            patient_id=request.patient_id,
            category_filter=request.category_filter,
            min_confidence=request.min_confidence,
            n_results=request.n_results,
        )
