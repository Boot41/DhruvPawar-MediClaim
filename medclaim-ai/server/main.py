from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api import router as api_router
from database import engine, Base

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Health Insurance Claim Assistant")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Health Insurance Claim Assistant API is running"}

