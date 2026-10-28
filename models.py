"""
Database models for hearing test state management.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./hearing_tests.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class HearingTest(Base):
    """Model for storing hearing test state and results."""
    __tablename__ = "hearing_tests"

    id = Column(String, primary_key=True, index=True)  # test_id
    phone = Column(String, index=True)
    call_id = Column(String, index=True)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer)
    correct_answers = Column(Integer, default=0)
    final_score = Column(Float, nullable=True)
    interpretation = Column(String, nullable=True)
    recommendation = Column(String, nullable=True)
    
    # JSON array of answers: [{"step": 1, "expected": "1", "pressed": "1", "correct": true}]
    answers = Column(JSON, default=[])
    
    # JSON array of used audio clip indices to avoid repetition
    used_audio_indices = Column(JSON, default=[])
    
    is_finished = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "test_id": self.id,
            "phone": self.phone,
            "call_id": self.call_id,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "correct_answers": self.correct_answers,
            "final_score": self.final_score,
            "interpretation": self.interpretation,
            "recommendation": self.recommendation,
            "is_finished": self.is_finished,
            "answers": self.answers,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
