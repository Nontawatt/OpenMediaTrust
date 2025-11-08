"""
Main FastAPI application for OpenMediaTrust.

Provides REST API for manifest creation, verification, and management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import manifests, verification, workflow, admin

app = FastAPI(
    title="OpenMediaTrust API",
    description="Enterprise C2PA Manifest System with Post-Quantum Cryptography",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(manifests.router, prefix="/api/v1", tags=["Manifests"])
app.include_router(verification.router, prefix="/api/v1", tags=["Verification"])
app.include_router(workflow.router, prefix="/api/v1", tags=["Workflow"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OpenMediaTrust API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-11-08T00:00:00Z"}
