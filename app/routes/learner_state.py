from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardProgress, User, UserSkill


router = APIRouter(tags=["Learner State"])


@router.get("/learner-state/{user_id}")
def get_learner_state(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    skills = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id)
        .all()
    )
    card_progress = (
        db.query(CardProgress)
        .filter(CardProgress.user_id == user_id)
        .all()
    )

    progress_count = len(card_progress)
    average_mastery = (
        sum(progress.mastery_score or 0.0 for progress in card_progress)
        / progress_count
        if progress_count
        else 0.0
    )
    average_accuracy = (
        sum(
            (progress.correct_answers or 0) / progress.total_questions
            if progress.total_questions
            else 0.0
            for progress in card_progress
        )
        / progress_count
        if progress_count
        else 0.0
    )
    average_build_score = (
        sum(progress.build_score or 0.0 for progress in card_progress)
        / progress_count
        if progress_count
        else 0.0
    )

    return {
        "user_id": user.id,
        "profile": {
            "name": user.name,
            "goal": user.goal,
            "level": user.level,
            "learning_style": user.learning_style,
        },
        "skills": [
            {
                "skill": skill.skill,
                "interest_score": round(skill.interest_score or 0.0, 4),
                "skill_score": round(skill.skill_score or 0.0, 4),
                "completion_rate": round(skill.completion_rate or 0.0, 4),
                "skip_rate": round(skill.skip_rate or 0.0, 4),
            }
            for skill in skills
        ],
        "metrics": {
            "cards_attempted": progress_count,
            "cards_completed": sum(
                1 for progress in card_progress if progress.completed_at is not None
            ),
            "average_mastery": round(average_mastery, 4),
            "average_accuracy": round(average_accuracy, 4),
            "average_build_score": round(average_build_score, 4),
            "total_attempts": sum(progress.attempt_count or 0 for progress in card_progress),
        },
    }
