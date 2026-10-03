import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..services.card_recommender import get_card_recommendations
from ..database import get_db
from ..models import (
    LearningCard,
    LearningStep,
    CardProgress,
    StepProgress,
    User,
    RecommendationHistory
)


router = APIRouter(prefix="/cards", tags=["Learning Cards"])
history_router = APIRouter(tags=["Recommendation History"])
logger = logging.getLogger(__name__)

@router.get("/feed/{user_id}")
def get_card_feed(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    recommendations = get_card_recommendations(
        db,
        user_id,
        limit=5
    )

    feed_session_id = str(uuid.uuid4())
    try:
        db.add_all([
            RecommendationHistory(
                user_id=user_id,
                card_id=item["card"].id,
                feed_session_id=feed_session_id,
                completion_probability=item["completion_probability"],
                performance_score=item["performance_score"],
                interest_score=item["interest_score"],
                skill_fit_score=item["skill_fit_score"],
                progress_score=item["progress_score"],
                preference_score=item["preference_score"],
                final_score=item["score"],
                rank=rank,
            )
            for rank, item in enumerate(recommendations, start=1)
        ])
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Could not save recommendation history for user %s", user_id
        )

    return {
        "user_id": user_id,
        "count": len(recommendations),
        "cards": [
            {
                "id": item["card"].id,
                "title": item["card"].title,
                "subject": item["card"].subject,
                "topic": item["card"].topic,
                "concept": item["card"].concept,
                "skill": item["card"].skill,
                "difficulty": item["card"].difficulty,
                "ideal_time": item["card"].ideal_time,
                "progress_value": item["card"].progress_value,
                "description": item["card"].description,
                "recommendation_score": item["score"],
                "completion_probability": item["completion_probability"]
            }
            for item in recommendations
        ]
    }


@history_router.get("/recommendations/history/{user_id}")
def get_recommendation_history(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    history = (
        db.query(RecommendationHistory)
        .filter(RecommendationHistory.user_id == user_id)
        .order_by(
            RecommendationHistory.created_at.desc(),
            RecommendationHistory.id.desc()
        )
        .all()
    )

    return {
        "user_id": user_id,
        "count": len(history),
        "history": [
            {
                "id": item.id,
                "card_id": item.card_id,
                "feed_session_id": item.feed_session_id,
                "rank": item.rank,
                "completion_probability": item.completion_probability,
                "performance_score": item.performance_score,
                "interest_score": item.interest_score,
                "skill_fit_score": item.skill_fit_score,
                "progress_score": item.progress_score,
                "preference_score": item.preference_score,
                "final_score": item.final_score,
                "created_at": item.created_at,
            }
            for item in history
        ],
    }

@router.get("/{card_id}")
def get_card(
    card_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    card = (
        db.query(LearningCard)
        .filter(LearningCard.id == card_id)
        .first()
    )

    if not card:
        raise HTTPException(
            status_code=404,
            detail="Learning card not found"
        )

    progress = (
        db.query(CardProgress)
        .filter(
            CardProgress.user_id == user_id,
            CardProgress.card_id == card_id
        )
        .first()
    )

    if not progress:
        progress = CardProgress(
            user_id=user_id,
            card_id=card_id,
            started_at=datetime.utcnow(),
            ideal_time=card.ideal_time
        )

        db.add(progress)
        db.commit()
        db.refresh(progress)

    steps = (
        db.query(LearningStep)
        .filter(LearningStep.card_id == card_id)
        .order_by(LearningStep.order)
        .all()
    )

    step_progress_records = (
        db.query(StepProgress)
        .filter(
            StepProgress.user_id == user_id,
            StepProgress.card_id == card_id
        )
        .all()
    )

    step_progress_map = {
        record.step_id: record
        for record in step_progress_records
    }

    return {
        "card": {
            "id": card.id,
            "title": card.title,
            "subject": card.subject,
            "topic": card.topic,
            "concept": card.concept,
            "skill": card.skill,
            "difficulty": card.difficulty,
            "ideal_time": card.ideal_time,
            "progress_value": card.progress_value,
            "description": card.description
        },
        "progress": {
            "started_at": progress.started_at,
            "completed_at": progress.completed_at,
            "watch_completed": progress.watch_completed,
            "solve_completed": progress.solve_completed,
            "build_completed": progress.build_completed,
            "correct_answers": progress.correct_answers,
            "total_questions": progress.total_questions,
            "time_spent": progress.time_spent,
            "ideal_time": progress.ideal_time,
            "comprehension_score": progress.comprehension_score,
            "mastery_score": progress.mastery_score,
            "attempt_count": progress.attempt_count,
            "needs_revision": progress.needs_revision
        },
        "steps": [
            {
                "id": step.id,
                "order": step.order,
                "type": step.type,
                "title": step.title,
                "content": step.content,
                "question": step.question,
                "options": step.options,
                "answer": step.answer,
                "starter_code": step.starter_code,
                "expected_output": step.expected_output,
                "duration": step.duration,

                "progress": {
                    "completed": (
                        step_progress_map[step.id].completed
                        if step.id in step_progress_map
                        else False
                    ),
                    "correct": (
                        step_progress_map[step.id].correct
                        if step.id in step_progress_map
                        else None
                    ),
                    "build_score": (
                        step_progress_map[step.id].build_score
                        if step.id in step_progress_map
                        else None
                    ),
                    "time_spent": (
                        step_progress_map[step.id].time_spent
                        if step.id in step_progress_map
                        else 0
                    ),
                    "attempt_count": (
                        step_progress_map[step.id].attempt_count
                        if step.id in step_progress_map
                        else 0
                    )
                }
            }
            for step in steps
        ]
    }
