# backend/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime # type: ignore
from sqlalchemy.orm import declarative_base, relationship # type: ignore
from datetime import datetime

Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(256))
    email = Column(String(256))
    phone = Column(String(64))
    years_experience = Column(Integer)
    desired_position = Column(String(256))
    location = Column(String(256))
    tech_stack_raw = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("QuestionBlock", back_populates="candidate", cascade="all, delete-orphan")

class QuestionBlock(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    technology = Column(String(128))
    difficulty = Column(String(32))
    questions_json = Column(Text)  # JSON array of questions as text
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="questions")
