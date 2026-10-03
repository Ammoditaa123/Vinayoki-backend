from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from .database import Base


# -------------------------
# USER
# -------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    level = Column(String, nullable=False)
    learning_style = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("UserSkill", back_populates="user")
    interactions = relationship("Interaction", back_populates="user")
    card_progress = relationship("CardProgress", back_populates="user")
    learning_preferences = relationship(
        "LearningPreferences",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


# -------------------------
# USER SKILL
# -------------------------

class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill = Column(String, nullable=False)

    interest_score = Column(Float, default=0.5)
    skill_score = Column(Float, default=0.3)
    completion_rate = Column(Float, default=0.0)
    skip_rate = Column(Float, default=0.0)

    user = relationship("User", back_populates="skills")

class LearningPreferences(Base):
    __tablename__ = "learning_preferences"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    watch_weight = Column(Float, default=0.20)
    solve_weight = Column(Float, default=0.20)
    build_weight = Column(Float, default=0.20)
    explore_weight = Column(Float, default=0.40)

# -------------------------
# OLD CONTENT SYSTEM
# -------------------------

class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    skill = Column(String, nullable=False)
    type = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)

    question = Column(Text, nullable=True)
    options = Column(Text, nullable=True)
    answer = Column(String, nullable=True)

    progress_value = Column(Float, default=1.0)

    interactions = relationship("Interaction", back_populates="content")


# -------------------------
# OLD INTERACTION SYSTEM
# -------------------------

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)

    action = Column(String, nullable=False)
    time_spent = Column(Integer, default=0)

    correct = Column(Boolean, nullable=True)
    completed = Column(Boolean, default=False)

    progress_earned = Column(Float, default=0.0)

    idempotency_key = Column(String, unique=True, nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    content = relationship("Content", back_populates="interactions")


# =========================================================
# NEW ADAPTIVE LEARNING SYSTEM
# =========================================================


# -------------------------
# LEARNING CARD
# -------------------------

class LearningCard(Base):
    __tablename__ = "learning_cards"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    subject = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    concept = Column(String, nullable=False, index=True)
    skill = Column(String, nullable=False, index=True)

    difficulty = Column(Integer, nullable=False)

    ideal_time = Column(Integer, nullable=False)

    progress_value = Column(Float, default=1.0)

    description = Column(Text, nullable=False)

    steps = relationship(
        "LearningStep",
        back_populates="card",
        cascade="all, delete-orphan",
        order_by="LearningStep.order"
    )

    progress = relationship(
        "CardProgress",
        back_populates="card"
    )


# -------------------------
# LEARNING STEP
# -------------------------

class LearningStep(Base):
    __tablename__ = "learning_steps"

    id = Column(Integer, primary_key=True, index=True)

    card_id = Column(
        Integer,
        ForeignKey("learning_cards.id"),
        nullable=False
    )

    order = Column(Integer, nullable=False)

    type = Column(String, nullable=False)

    title = Column(String, nullable=False)

    content = Column(Text, nullable=True)

    question = Column(Text, nullable=True)

    options = Column(Text, nullable=True)

    answer = Column(String, nullable=True)

    starter_code = Column(Text, nullable=True)

    expected_output = Column(Text, nullable=True)

    duration = Column(Integer, default=1)

    card = relationship(
        "LearningCard",
        back_populates="steps"
    )


# -------------------------
# CARD PROGRESS
# -------------------------

class CardProgress(Base):
    __tablename__ = "card_progress"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    card_id = Column(
        Integer,
        ForeignKey("learning_cards.id"),
        nullable=False
    )

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    watch_completed = Column(Boolean, default=False)
    solve_completed = Column(Boolean, default=False)
    build_completed = Column(Boolean, default=False)
    correct_answers = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    build_score = Column(Float, default=0.0)
    time_spent = Column(Integer, default=0)
    ideal_time = Column(Integer, default=0)
    comprehension_score = Column(Float, default=0.0)
    mastery_score = Column(Float, default=0.0)
    attempt_count = Column(Integer, default=0)
    needs_revision = Column(Boolean, default=False)

    user = relationship(
        "User",
        back_populates="card_progress"
    )

    card = relationship(
        "LearningCard",
        back_populates="progress"
    )

class StepProgress(Base):
    __tablename__ = "step_progress"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    card_id = Column(
        Integer,
        ForeignKey("learning_cards.id"),
        nullable=False
    )

    step_id = Column(
        Integer,
        ForeignKey("learning_steps.id"),
        nullable=False
    )

    completed = Column(Boolean, default=False)

    correct = Column(Boolean, nullable=True)

    build_score = Column(Float, nullable=True)

    time_spent = Column(Integer, default=0)

    attempt_count = Column(Integer, default=0)


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("learning_cards.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    feed_session_id = Column(String, nullable=False, index=True)

    completion_probability = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=False)
    interest_score = Column(Float, nullable=False)
    skill_fit_score = Column(Float, nullable=False)
    progress_score = Column(Float, nullable=False)
    preference_score = Column(Float, nullable=False)

    final_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
