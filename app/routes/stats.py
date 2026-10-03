from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import User, CardProgress, StepProgress

router = APIRouter(
    prefix="/stats",
    tags=["Stats"]
)


@router.get("/{user_id}")
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    card_progress = (
        db.query(CardProgress)
        .filter(CardProgress.user_id == user_id)
        .all()
    )

    step_progress = (
        db.query(StepProgress)
        .filter(StepProgress.user_id == user_id)
        .all()
    )

    total_time = sum(
        progress.time_spent or 0
        for progress in card_progress
    )

    learning_time = sum(
        progress.time_spent or 0
        for progress in step_progress
        if progress.completed
    )

    cards_completed = sum(
        1
        for progress in card_progress
        if progress.completed_at is not None
    )

    steps_completed = sum(
        1
        for progress in step_progress
        if progress.completed
    )

    passive_time = max(
        total_time - learning_time,
        0
    )

    return {
        "user_id": user_id,
        "total_time": total_time,
        "learning_time": learning_time,
        "passive_time": passive_time,
        "cards_completed": cards_completed,
        "steps_completed": steps_completed
    }