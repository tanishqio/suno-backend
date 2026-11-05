"""
Database models for hearing test state management.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class HearingTest(Base):
    """Model for storing hearing test state and results."""
    __tablename__ = "hearing_tests"

    id = Column(String, primary_key=True, index=True)
    phone = Column(String, index=True)
    call_id = Column(String, index=True)
    language = Column(String)
    total_trials = Column(Integer)
    correct_trials = Column(Integer, default=0)
    final_score = Column(Float, nullable=True)
    interpretation = Column(String, nullable=True)
    recommendation = Column(String, nullable=True)

    # One entry per trial, the last one is the trial in progress. Always assign a new list:
    # in-place changes to a JSON column are not saved.
    # {"trial": 1, "digits": "695", "files": [...], "pressed": "695", "correct": true, "answered_at": "..."}
    trials = Column(JSON, default=list)

    is_finished = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrialAudio(Base):
    """Merged MP3 for one trial, served to Bolna from /audio/{test_id}/{trial}.mp3."""
    __tablename__ = "trial_audio"

    test_id = Column(String, primary_key=True)
    trial = Column(Integer, primary_key=True)
    mp3 = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
