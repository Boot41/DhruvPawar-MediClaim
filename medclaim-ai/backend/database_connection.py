"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from database import Base
from typing import Generator

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medclaim.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables and seed data."""
    create_tables()
    
    # Seed popular vendors
    from database import Vendor
    db = SessionLocal()
    
    try:
        # Check if vendors already exist
        if db.query(Vendor).count() == 0:
            vendors = [
                Vendor(name="star_health", display_name="Star Health Insurance", form_template_url="https://example.com/star_health_form.pdf"),
                Vendor(name="hdfc_ergo", display_name="HDFC ERGO", form_template_url="https://example.com/hdfc_ergo_form.pdf"),
                Vendor(name="icici_lombard", display_name="ICICI Lombard", form_template_url="https://example.com/icici_lombard_form.pdf"),
                Vendor(name="new_india", display_name="New India Assurance", form_template_url="https://example.com/new_india_form.pdf"),
                Vendor(name="max_bupa", display_name="Max Bupa (Niva Bupa)", form_template_url="https://example.com/max_bupa_form.pdf"),
            ]
            
            for vendor in vendors:
                db.add(vendor)
            
            db.commit()
            print("✓ Seeded popular vendors")
    except Exception as e:
        print(f"Error seeding vendors: {e}")
    finally:
        db.close()
