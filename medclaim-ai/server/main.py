from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from server.config.database import engine, Base
from server.api.api_admin import router as admin_router
from server.api.api_chat import router as chat_router
from server.api.api_claims import router as claims_router
from server.api.api_documents import router as documents_router
from server.api.api_users import router as users_router
import server.models.models  # Ensure all models are registered
import os

# ==========================
# CONFIG
# ==========================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# ==========================
# APP INITIALIZATION
# ==========================
app = FastAPI(title="Health Insurance Claim Assistant")

# ==========================
# CORS CONFIGURATION
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# DATABASE INITIALIZATION (Dev Only)
# ==========================
# In production, use Alembic migrations instead of create_all
if os.getenv("ENV", "development") == "development":
    Base.metadata.create_all(bind=engine)

# ==========================
# ROUTER REGISTRATION
# ==========================
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(claims_router, prefix="/api/claims", tags=["Claims"])
app.include_router(chat_router, prefix="/api/chat", tags=["AI Chat Assistant"])

# ==========================
# HEALTH CHECK ROUTE
# ==========================
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Root Route
@app.get("/")
async def root():
    return {"message": "Health Insurance Claim Assistant API is running"}
