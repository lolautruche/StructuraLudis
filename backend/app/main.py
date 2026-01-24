"""
FastAPI application entry point.

Similar to Symfony's public/index.php + Kernel.
"""
from fastapi import FastAPI

from app.api.v1.endpoint import exhibition, organization

app = FastAPI(
    title="Structura Ludis API",
    version="0.1.0",
    description="Backend for RPG Convention Management",
)

# Include routers
app.include_router(
    organization.router,
    prefix="/api/v1/organizations",
    tags=["Organizations"],
)
app.include_router(
    exhibition.router,
    prefix="/api/v1/exhibitions",
    tags=["Exhibitions"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}