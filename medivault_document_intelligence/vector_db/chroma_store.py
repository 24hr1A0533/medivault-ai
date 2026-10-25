"""
ChromaDB Vector Store Manager
Manages production persistent ChromaDB collections, dense vector indexing,
metadata payload filtering, and semantic similarity search over clinical records.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from ..schemas.document_schema import (
    StructuredMedicalDocument,
    VectorSearchResultItem,
    VectorQueryResponse,
    DocumentCategory,
)

logger = logging.getLogger("document_intelligence.chroma")


class ChromaVectorStore:
    """
    Production vector repository using ChromaDB.
    Maintains persistent vector indices with cosine distance metrics.
    """

    DEFAULT_COLLECTION_NAME = "medivault_clinical_records"

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or os.path.join(
            os.path.expanduser("~"), ".medivault", "chromadb"
        )
        os.makedirs(self.persist_directory, exist_ok=True)
        self._client = None
        self._collection = None
        self._init_chroma()

    def _init_chroma(self):
        """Initializes ChromaDB PersistentClient."""
        try:
            import chromadb
            from chromadb.config import Settings
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
            # Create or get collection with cosine similarity space
            self._collection = self._client.get_or_create_collection(
                name=self.DEFAULT_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB persistent client loaded at '{self.persist_directory}'.")
        except Exception as exc:
            logger.warning(f"ChromaDB initialization notice: {str(exc)}. In-memory vector index fallback active.")
            self._client = None
            self._collection = None
            self._in_memory_docs: Dict[str, Dict[str, Any]] = {}

    def is_connected(self) -> bool:
        return self._collection is not None or hasattr(self, "_in_memory_docs")

    def index_document(
        self,
        doc: StructuredMedicalDocument,
        embedding: List[float],
        semantic_passage: str,
    ) -> str:
        """
        Indexes a structured medical document into ChromaDB.
        """
        doc_id = doc.document_id

        # Format metadata payload (ChromaDB supports primitive types: str, int, float, bool)
        test_names_csv = ",".join(t.test_name for t in doc.medical_data.tests)
        medicines_csv = ",".join(rx.medicine for rx in doc.prescriptions)

        metadata = {
            "document_id": doc.document_id,
            "patient_id": doc.patient_id or "UNKNOWN",
            "category": doc.medical_data.category.value,
            "hospital": doc.medical_data.hospital or "UNKNOWN",
            "report_date": str(doc.medical_data.report_date) if doc.medical_data.report_date else "",
            "verification_status": doc.verification_status.value,
            "overall_confidence": float(doc.overall_confidence),
            "test_names": test_names_csv[:500],
            "medicines": medicines_csv[:500],
            "patient_name": doc.patient_details.name or "UNKNOWN",
        }

        if self._collection:
            try:
                self._collection.upsert(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[semantic_passage],
                    metadatas=[metadata],
                )
                logger.info(f"Document '{doc_id}' indexed in ChromaDB successfully.")
                return doc_id
            except Exception as exc:
                logger.error(f"ChromaDB upsert error: {str(exc)}")

        # Fallback in-memory index
        if not hasattr(self, "_in_memory_docs"):
            self._in_memory_docs = {}
        self._in_memory_docs[doc_id] = {
            "id": doc_id,
            "embedding": embedding,
            "document": semantic_passage,
            "metadata": metadata,
        }
        return doc_id

    def search(
        self,
        query_embedding: List[float],
        query_text: str,
        patient_id: Optional[str] = None,
        category_filter: Optional[DocumentCategory] = None,
        min_confidence: Optional[float] = 0.0,
        n_results: int = 5,
    ) -> VectorQueryResponse:
        """
        Executes semantic vector search using cosine similarity.
        """
        where_clauses = {}
        if patient_id:
            where_clauses["patient_id"] = patient_id
        if category_filter:
            where_clauses["category"] = category_filter.value

        where_filter = where_clauses if where_clauses else None

        results_list: List[VectorSearchResultItem] = []

        if self._collection:
            try:
                res = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_filter,
                )

                if res and res.get("ids") and len(res["ids"][0]) > 0:
                    for i in range(len(res["ids"][0])):
                        dist = res["distances"][0][i] if res.get("distances") else 0.0
                        # Cosine distance in ChromaDB is 1 - cosine_similarity
                        sim_score = round(max(0.0, 1.0 - dist), 4)

                        meta = res["metadatas"][0][i] if res.get("metadatas") else {}
                        doc_text = res["documents"][0][i] if res.get("documents") else ""

                        conf = meta.get("overall_confidence", 1.0)
                        if min_confidence and conf < min_confidence:
                            continue

                        results_list.append(
                            VectorSearchResultItem(
                                document_id=res["ids"][0][i],
                                patient_id=meta.get("patient_id"),
                                similarity_score=sim_score,
                                distance=round(dist, 4),
                                category=meta.get("category", "OTHER"),
                                report_date=meta.get("report_date"),
                                hospital=meta.get("hospital"),
                                content_snippet=doc_text[:300] + ("..." if len(doc_text) > 300 else ""),
                                metadata=meta,
                            )
                        )

                return VectorQueryResponse(
                    query=query_text,
                    total_found=len(results_list),
                    results=results_list,
                )
            except Exception as exc:
                logger.error(f"Chroma query execution error: {str(exc)}")

        # Fallback in-memory vector search
        if hasattr(self, "_in_memory_docs"):
            import numpy as np
            q_vec = np.array(query_embedding, dtype=np.float32)

            scored = []
            for doc_id, item in self._in_memory_docs.items():
                meta = item["metadata"]
                if patient_id and meta.get("patient_id") != patient_id:
                    continue
                if category_filter and meta.get("category") != category_filter.value:
                    continue
                if min_confidence and meta.get("overall_confidence", 1.0) < min_confidence:
                    continue

                d_vec = np.array(item["embedding"], dtype=np.float32)
                sim = float(np.dot(q_vec, d_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(d_vec) + 1e-9))
                scored.append((sim, item))

            scored.sort(key=lambda x: x[0], reverse=True)
            for sim, item in scored[:n_results]:
                meta = item["metadata"]
                doc_text = item["document"]
                dist = 1.0 - sim
                results_list.append(
                    VectorSearchResultItem(
                        document_id=item["id"],
                        patient_id=meta.get("patient_id"),
                        similarity_score=round(max(0.0, min(1.0, (sim + 1.0) / 2.0)), 4),
                        distance=round(dist, 4),
                        category=meta.get("category", "OTHER"),
                        report_date=meta.get("report_date"),
                        hospital=meta.get("hospital"),
                        content_snippet=doc_text[:300] + ("..." if len(doc_text) > 300 else ""),
                        metadata=meta,
                    )
                )

        return VectorQueryResponse(
            query=query_text,
            total_found=len(results_list),
            results=results_list,
        )
