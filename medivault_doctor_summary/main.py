"""
FastAPI application entrypoint for MediVault Doctor Consultation Summary Engine.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from medivault_doctor_summary.api.routes import router as summary_router

app = FastAPI(
    title="MediVault Doctor Consultation Summary Engine",
    description="Generates concise, medically accurate, citation-backed briefing notes for physician consultations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summary_router)

@app.get("/")
def root():
    return {
        "service": "MediVault Doctor Consultation Summary Engine",
        "status": "online",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("medivault_doctor_summary.main:app", host="0.0.0.0", port=8005, reload=True)
