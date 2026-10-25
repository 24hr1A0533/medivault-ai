"""
FastAPI application entrypoint for MediVault Medical LLM Microservice.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from medivault_medical_llm.api.routes import router as medical_llm_router

app = FastAPI(
    title="MediVault Medical LLM",
    description="Unified clinical AI platform powered by Qwen 2.5 7B, BGE Large, ChromaDB, and vLLM.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medical_llm_router)

@app.get("/")
def root():
    return {
        "service": "MediVault Medical LLM",
        "model": "Qwen 2.5 7B",
        "embedding": "BGE Large",
        "vector_database": "ChromaDB",
        "inference": "vLLM",
        "status": "online",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("medivault_medical_llm.main:app", host="0.0.0.0", port=8006, reload=True)
