"""
MediVault Patient-Specific RAG LLM Microservice
Production ASGI entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from medivault_patient_rag.api.routes import router as rag_router

app = FastAPI(
    title="MediVault Patient-Specific RAG LLM System",
    description="Production-grade clinical RAG microservice with strict tenant isolation, multi-feature clinical reasoning (Explain, Summarize, Compare, Timeline, Doctor Summary), and verified source citations.",
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

app.include_router(rag_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "MediVault Patient-Specific RAG LLM System",
        "version": "1.0.0",
        "tenant_isolation": "MANDATORY_PATIENT_FILTERING",
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("medivault_patient_rag.main:app", host="0.0.0.0", port=8002, reload=True)
