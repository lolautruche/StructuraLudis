"""
FastAPI application entry point.
"""
from fastapi import FastAPI

from app.api.v1.endpoint import admin, auth, exhibition, game, group, notification, organization, zone, game_session, operations, user

app = FastAPI(
    title="Structura Ludis API",
    version="0.1.0",
    description="Backend for RPG Convention Management",
)

# Include routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)
app.include_router(
    organization.router,
    prefix="/api/v1/organizations",
    tags=["Organizations"],
)
app.include_router(
    group.router,
    prefix="/api/v1/groups",
    tags=["Groups"],
)
app.include_router(
    exhibition.router,
    prefix="/api/v1/exhibitions",
    tags=["Exhibitions"],
)
app.include_router(
    zone.router,
    prefix="/api/v1/zones",
    tags=["Zones"],
)
app.include_router(
    game_session.router,
    prefix="/api/v1/sessions",
    tags=["Game Sessions"],
)
app.include_router(
    game.router,
    prefix="/api/v1/games",
    tags=["Games"],
)
app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"],
)
app.include_router(
    operations.router,
    prefix="/api/v1/ops",
    tags=["Operations"],
)
app.include_router(
    user.router,
    prefix="/api/v1/users",
    tags=["Users"],
)
app.include_router(
    notification.router,
    prefix="/api/v1",
    tags=["Notifications"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}