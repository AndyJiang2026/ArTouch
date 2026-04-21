# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create FastAPI main application with startup initialization
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import all routers
from app.api.auth import router as auth_router
from app.api.cultural_products import router as cultural_products_router
from app.api.dashboard import router as dashboard_router
from app.api.nfc import router as nfc_router
from app.api.nfc_tags import router as nfc_tags_router
from app.api.sku_instances import router as sku_instances_router
from app.api.skus import router as skus_router
from app.api.static_protected import router as static_protected_router
from app.api.users import router as users_router
from app.api.videos import router as videos_router
from app.config import settings
from app.core.security import get_password_hash
from app.database import Base, engine
from app.models import SessionLocal, User


def init_db():
    """Initialize database and create default admin user.

    Admin user is created only if ADMIN_SETUP_TOKEN environment variable is set.
    This prevents accidental admin creation in production.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Check if admin user exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # Only create admin if ADMIN_SETUP_TOKEN is set
            setup_token = os.getenv("ADMIN_SETUP_TOKEN", "")
            if not setup_token:
                print("WARNING: Admin user not created. Set ADMIN_SETUP_TOKEN env var to create initial admin.")
                return

            # Verify setup token matches expected value
            expected_token = os.getenv("ADMIN_SETUP_TOKEN", "artouch-admin-setup")
            if setup_token != expected_token:
                print("WARNING: Invalid ADMIN_SETUP_TOKEN. Admin user not created.")
                return

            # Get admin password from environment or generate temp password
            admin_password = os.getenv("ADMIN_INITIAL_PASSWORD", "")
            if not admin_password:
                import secrets
                admin_password = secrets.token_urlsafe(12)
                print(f"WARNING: No ADMIN_INITIAL_PASSWORD set. Generated temp password: {admin_password}")
                print("Please change this password immediately after first login.")

            # Create admin user with provided or generated password
            admin = User(
                username="admin",
                password_hash=get_password_hash(admin_password),
                role="admin",
                is_active=True,
                is_first_login=True,
            )
            db.add(admin)
            db.commit()
            print("Admin user created: username=admin (password provided via env or generated)")
        else:
            print("Admin user already exists")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    print(f"ArtTouch NFC System started on {datetime.utcnow()}")
    yield
    # Shutdown
    print(f"ArtTouch NFC System stopped on {datetime.utcnow()}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ArtTouch NFC互动视频系统后端API",
    lifespan=lifespan,
)

# CORS middleware - origins configured via environment variable
def _get_cors_origins() -> list:
    """Parse ALLOWED_ORIGINS from environment variable (comma-separated)."""
    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]
    # Default origins if not configured
    return [
        "https://www.qiangguoshijie.com.cn",
        "https://qiangguoshijie.com.cn",
    ]


ALLOWED_ORIGINS = _get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(_request: Request, exc: ValueError):
    """Handle ValueError (e.g. invalid date/week/month format) as 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Include routers
app.include_router(auth_router)
app.include_router(cultural_products_router)
app.include_router(videos_router)
app.include_router(skus_router)
app.include_router(sku_instances_router)
app.include_router(nfc_tags_router)
app.include_router(dashboard_router)
app.include_router(nfc_router)
app.include_router(users_router)

# Conditional static file serving
if settings.PROTECT_STATIC_FILES:
    # Protected static files with signed URLs
    app.include_router(static_protected_router)
else:
    # Public static files (for NFC play flow - no auth required)
    app.mount("/videos", StaticFiles(directory=str(settings.VIDEO_DIR)), name="videos")
    app.mount("/covers", StaticFiles(directory=str(settings.COVER_DIR)), name="covers")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
