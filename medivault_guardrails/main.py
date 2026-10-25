"""
FastAPI application entrypoint for MediVault Medical AI Safety Guardrails Microservice.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from medivault_guardrails.api.routes import router as guardrail_router

app = FastAPI(
    title="MediVault AI Medical Safety Guardrails",
    description="Multi-tier safety layer enforcing educational boundaries, prompt shielding, and output filtering.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guardrail_router)

@app.get("/")
def root():
    return {
        "service": "MediVault AI Medical Safety Guardrails",
        "status": "online",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("medivault_guardrails.main:app", host="0.0.0.0", port=8003, reload=True)
