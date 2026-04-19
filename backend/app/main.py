# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create FastAPI main application with startup initialization
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.security import get_password_hash
from app.models import Base, engine, SessionLocal, User, CulturalProduct, Video, SKU, NFCTag, TagClick

# Import all routers
from app.api.auth import router as auth_router
from app.api.cultural_products import router as cultural_products_router
from app.api.videos import router as videos_router
from app.api.skus import router as skus_router
from app.api.nfc_tags import router as nfc_tags_router
from app.api.dashboard import router as dashboard_router
from app.api.nfc import router as nfc_router


def init_db():
    """Initialize database and create default admin user."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Check if admin user exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # Create default admin user
            admin = User(
                username="admin",
                password_hash=get_password_hash("123456"),
                role="admin",
                is_active=True,
                is_first_login=True,
            )
            db.add(admin)
            db.commit()
            print("Default admin user created: username=admin, password=123456")
        else:
            print("Admin user already exists")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
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

# CORS middleware - whitelist allowed origins
ALLOWED_ORIGINS = [
    "https://www.qiangguoshijie.com.cn",
    "https://qiangguoshijie.com.cn",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
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
app.include_router(nfc_tags_router)
app.include_router(dashboard_router)
app.include_router(nfc_router)


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
