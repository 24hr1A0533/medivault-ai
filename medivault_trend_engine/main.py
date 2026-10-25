"""
FastAPI application entrypoint for MediVault Medical Trend Analysis Engine.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from medivault_trend_engine.api.routes import router as trend_router

app = FastAPI(
    title="MediVault Medical Trend Analysis Engine",
    description="Production-grade clinical biomarker trend analysis, SVG graph generation, deterioration alerts, and doctor-ready summaries.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trend_router)

@app.get("/")
def root():
    return {
        "service": "MediVault Medical Trend Analysis Engine",
        "status": "online",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("medivault_trend_engine.main:app", host="0.0.0.0", port=8004, reload=True)
