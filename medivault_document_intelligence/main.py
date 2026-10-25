"""
MediVault Healthcare Document Intelligence Microservice
Production ASGI entry point hosting the document intelligence pipeline.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from medivault_document_intelligence.api.routes import router as doc_intel_router

app = FastAPI(
    title="MediVault Healthcare Document Intelligence Service",
    description="Production-grade AI microservice converting medical documents (PDF/JPG/PNG) into structured knowledge with PaddleOCR, BioBERT/ClinicalBERT, BAAI BGE Large, and ChromaDB.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(doc_intel_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "MediVault Healthcare Document Intelligence",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("medivault_document_intelligence.main:app", host="0.0.0.0", port=8001, reload=True)
