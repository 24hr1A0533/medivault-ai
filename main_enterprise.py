"""
MediVault AI Commercial Hospital Operating System (HOS) Master Application.
Integrates Multi-Tenant SaaS, FHIR R4 Server, SMART on FHIR, HL7 MLLP Gateway,
Enterprise Security, Clinical Timeline, Visual Triage, and Sub-2s Emergency Case File Engine.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.tenant_service.tenant_controller import tenant_router
from services.tenant_service.tenant_middleware import TenantContextMiddleware
from services.ehr_gateway.fhir_server import fhir_router
from services.ehr_gateway.smart.smart_launch import smart_router
from services.emergency_service.emergency_engine import EmergencyCaseFileEngine
from services.triage_service.visual_triage import VisualTriageAI
from services.timeline_service.timeline_engine import ClinicalTimelineEngine


def create_enterprise_app() -> FastAPI:
    app = FastAPI(
        title="MediVault Hospital Operating System (HOS)",
        version="2.5.0",
        description="Commercially Deployable Hospital Information System & AI Intelligence Backbone",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Environment-driven CORS Origin Whitelist
    import os
    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    if env_origins:
        allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    else:
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://hospital.medivault.health",
            "https://console.medivault.health",
            "https://ambulance.medivault.health",
        ]

    # Enforce W3C compliance: Disallow wildcard with credentials
    if "*" in allowed_origins:
        allowed_origins = [o for o in allowed_origins if o != "*"]

    # Secure CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "X-SuperAdmin-Key", "X-User-Role", "X-Requested-With"],
        max_age=86400,
    )

    # Tenant Context Middleware
    app.add_middleware(TenantContextMiddleware)

    # Security Headers Middleware (CSP, HSTS, X-Content-Type-Options, Anti-Clickjacking)
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' https: http: ws: wss:; "
            "frame-ancestors 'none';"
        )
        return response

    # Mount Routers
    from services.emergency_service.emergency_controller import emergency_router
    app.include_router(tenant_router)
    app.include_router(fhir_router)
    app.include_router(smart_router)
    app.include_router(emergency_router)
    app.include_router(emergency_router, prefix="/api/v1")

    # Core Health Route
    @app.get("/health")
    def health_check():
        return {
            "status": "HEALTHY",
            "system": "MediVault Enterprise HOS",
            "version": "2.5.0",
            "tenants_active": True,
            "fhir_r4_ready": True,
            "smart_on_fhir_ready": True,
        }

    return app


app = create_enterprise_app()
