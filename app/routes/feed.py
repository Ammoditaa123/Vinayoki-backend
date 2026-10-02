from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Content, UserSkill, User
from ..services.recommender import (
    recommend_activities,
    get_recommendation_reason
)


router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)


@router.get("/")
def get_feed(
    db: Session = Depends(get_db)
):

    activities = db.query(Content).all()

    return {
        "count": len(activities),
        "activities": activities
    }


@router.get("/{user_id}")
def get_personalized_feed(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        return {
            "error": "User not found"
        }

    recommendations = recommend_activities(
        db,
        user_id,
        limit=5
    )

    result = []

    for item in recommendations:

        activity = item["activity"]

        skill_state = db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill == activity.skill
        ).first()

        reasons = get_recommendation_reason(
            user,
            activity,
            skill_state
        )

        result.append({
            "id": activity.id,
            "title": activity.title,
            "topic": activity.topic,
            "skill": activity.skill,
            "type": activity.type,
            "difficulty": activity.difficulty,
            "duration": activity.duration,
            "description": activity.description,
            "question": activity.question,
            "options": activity.options,
            "answer": activity.answer,
            "progress_value": activity.progress_value,
            "recommendation_score": item["score"],
            "completion_probability": item["completion_probability"],
            "why_this": reasons
        })

    return {
        "user_id": user_id,
        "count": len(result),
        "activities": result
    }