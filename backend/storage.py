# backend/storage.py
import os
import json
from pathlib import Path
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from backend.models import Base, Candidate, QuestionBlock
from datetime import datetime

DB_FILE = os.getenv("TALENTSCOUT_DB", "talentscout.db")
DB_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables (idempotent)
Base.metadata.create_all(bind=engine)

def save_candidate_with_questions(candidate: dict, question_blocks: list):
    """
    candidate: dict with keys full_name, email, phone, years_experience, desired_position, location, tech_stack_raw
    question_blocks: list of {"technology": "...", "difficulty": "...", "questions": [...]}
    """
    session = SessionLocal()
    try:
        c = Candidate(
            full_name=candidate.get("full_name"),
            email=candidate.get("email"),
            phone=candidate.get("phone"),
            years_experience=candidate.get("years_experience"),
            desired_position=candidate.get("desired_position"),
            location=candidate.get("location"),
            tech_stack_raw=candidate.get("tech_stack_raw"),
            created_at=datetime.utcnow()
        )
        session.add(c)
        session.flush()  # obtain c.id

        for block in question_blocks:
            qb = QuestionBlock(
                candidate_id=c.id,
                technology=block.get("technology"),
                difficulty=block.get("difficulty", "medium"),
                questions_json=json.dumps(block.get("questions", [])),
                created_at=datetime.utcnow()
            )
            session.add(qb)

        session.commit()
        return c.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def load_recent_with_questions(limit=10):
    """
    Returns list of dicts: [{candidate: {...}, question_blocks: [{...}, ...]}, ...]
    """
    session = SessionLocal()
    try:
        q = session.query(Candidate).order_by(Candidate.created_at.desc()).limit(limit).all()
        results = []
        for c in q:
            blocks = []
            for b in c.questions:
                blocks.append({
                    "technology": b.technology,
                    "difficulty": b.difficulty,
                    "questions": json.loads(b.questions_json or "[]"),
                    "created_at": b.created_at.isoformat()
                })
            results.append({
                "candidate": {
                    "id": c.id,
                    "full_name": c.full_name,
                    "email": c.email,
                    "phone": c.phone,
                    "years_experience": c.years_experience,
                    "desired_position": c.desired_position,
                    "location": c.location,
                    "tech_stack_raw": c.tech_stack_raw,
                    "created_at": c.created_at.isoformat()
                },
                "question_blocks": blocks
            })
        return results
    finally:
        session.close()
