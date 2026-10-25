"""
Global Configuration for MediVault Medical LLM Platform.
"""
import os
from pydantic import BaseModel, Field

class MediVaultConfig(BaseModel):
    # LLM & Inference configuration
    llm_model_name: str = Field(default="Qwen/Qwen2.5-7B-Instruct", description="Primary foundation model")
    vllm_api_base: str = Field(default="http://localhost:8000/v1")
    temperature: float = Field(default=0.1, description="Low temperature to prevent medical hallucinations")
    top_p: float = Field(default=0.9)
    max_tokens: int = Field(default=2048)
    
    # Embedding Configuration
    embedding_model_name: str = Field(default="BAAI/bge-large-en-v1.5", description="BGE Large dense embedder")
    embedding_dimension: int = Field(default=1024)
    
    # Vector Database Configuration
    vector_db_type: str = Field(default="ChromaDB")
    chroma_persist_directory: str = Field(default="./data/chroma_medical_llm")
    collection_name: str = Field(default="medivault_patient_records")
    
    # Security & HIPAA Governance
    hipaa_phi_masking: bool = Field(default=True)
    strict_tenant_isolation: bool = Field(default=True)
    zero_hallucination_policy: bool = Field(default=True)
    hallucination_threshold: float = Field(default=0.85, ge=0.0, le=1.0)

CONFIG = MediVaultConfig()
