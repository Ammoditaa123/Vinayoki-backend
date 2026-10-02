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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    goal = Column(String, nullable=False)

    level = Column(String, nullable=False)

    learning_style = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    skills = relationship(
        "UserSkill",
        back_populates="user"
    )

    interactions = relationship(
        "Interaction",
        back_populates="user"
    )


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    skill = Column(String, nullable=False)

    interest_score = Column(
        Float,
        default=0.5
    )

    skill_score = Column(
        Float,
        default=0.3
    )

    completion_rate = Column(
        Float,
        default=0.0
    )

    skip_rate = Column(
        Float,
        default=0.0
    )

    user = relationship(
        "User",
        back_populates="skills"
    )


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

    progress_value = Column(
        Float,
        default=1.0
    )

    interactions = relationship(
        "Interaction",
        back_populates="content"
    )


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    content_id = Column(
        Integer,
        ForeignKey("content.id"),
        nullable=False
    )

    action = Column(String, nullable=False)

    time_spent = Column(
        Integer,
        default=0
    )

    correct = Column(
        Boolean,
        nullable=True
    )

    completed = Column(
        Boolean,
        default=False
    )

    progress_earned = Column(
        Float,
        default=0.0
    )

    idempotency_key = Column(
        String,
        unique=True,
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="interactions"
    )

    content = relationship(
        "Content",
        back_populates="interactions"
    )