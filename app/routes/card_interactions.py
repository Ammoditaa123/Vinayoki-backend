from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    User,
    LearningCard,
    LearningStep,
    CardProgress,
    StepProgress
)


router = APIRouter(
    prefix="/card-interactions",
    tags=["Card Interactions"]
)


class CardInteraction(BaseModel):
    user_id: int
    card_id: int
    step_id: int
    action: str
    time_spent: int = 0
    correct: bool | None = None
    build_score: float | None = None


@router.post("/")
def record_card_interaction(
    data: CardInteraction,
    db: Session = Depends(get_db)
):
    # Check user
    user = db.query(User).filter(
        User.id == data.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check card
    card = db.query(LearningCard).filter(
        LearningCard.id == data.card_id
    ).first()

    if not card:
        raise HTTPException(
            status_code=404,
            detail="Learning card not found"
        )

    # Check step
    step = db.query(LearningStep).filter(
        LearningStep.id == data.step_id,
        LearningStep.card_id == data.card_id
    ).first()

    if not step:
        raise HTTPException(
            status_code=404,
            detail="Learning step not found for this card"
        )

    # Find or create step progress
    step_progress = db.query(StepProgress).filter(
        StepProgress.user_id == data.user_id,
        StepProgress.card_id == data.card_id,
        StepProgress.step_id == data.step_id
    ).first()

    if not step_progress:
        step_progress = StepProgress(
            user_id=data.user_id,
            card_id=data.card_id,
            step_id=data.step_id
        )

        db.add(step_progress)
        db.flush()

    step_progress.time_spent += max(0, data.time_spent)
    step_progress.attempt_count += 1
    # Find existing progress
    progress = db.query(CardProgress).filter(
        CardProgress.user_id == data.user_id,
        CardProgress.card_id == data.card_id
    ).first()

    # Create progress if this is the first interaction
    if not progress:
        progress = CardProgress(
            user_id=data.user_id,
            card_id=data.card_id,
            started_at=datetime.utcnow(),
            ideal_time=card.ideal_time
        )

        db.add(progress)
        db.flush()

    # Track time
    progress.time_spent += max(0, data.time_spent)

    # Track attempt
    progress.attempt_count += 1

    # -------------------------
    # STEP PROGRESS
    # -------------------------

    if data.action == "watch":

        step_progress.completed = True
        step_progress.completed_at = datetime.utcnow()

        progress.watch_completed = True

    elif data.action == "solve":

        step_progress.completed = True
        step_progress.completed_at = datetime.utcnow()
        step_progress.correct = data.correct

        progress.total_questions += 1

        if data.correct:
            progress.correct_answers += 1

        progress.solve_completed = True

    elif data.action == "build":

        step_progress.completed = True
        step_progress.completed_at = datetime.utcnow()

        if data.build_score is not None:
            step_progress.build_score = max(
                0.0,
                min(1.0, data.build_score)
            )

        progress.build_completed = True

        if data.build_score is not None:
            progress.build_score = max(
                0.0,
                min(1.0, data.build_score)
            )
        else:
            progress.build_score = 0.5

    elif data.action == "complete":

        step_progress.completed = True
        step_progress.completed_at = datetime.utcnow()

        progress.completed_at = datetime.utcnow()

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid action. Use watch, solve, build, or complete."
        )

    # -------------------------
    # CHECK CARD STAGE COMPLETION
    # -------------------------

    all_steps = db.query(LearningStep).filter(
        LearningStep.card_id == data.card_id
    ).all()

    step_progress_records = db.query(StepProgress).filter(
        StepProgress.user_id == data.user_id,
        StepProgress.card_id == data.card_id
    ).all()

    completed_step_ids = {
        record.step_id
        for record in step_progress_records
        if record.completed
    }

    watch_steps = [
        step for step in all_steps
        if step.type == "watch"
    ]

    solve_steps = [
        step for step in all_steps
        if step.type == "solve"
    ]

    build_steps = [
        step for step in all_steps
        if step.type == "build"
    ]

    progress.watch_completed = (
        len(watch_steps) > 0
        and all(
            step.id in completed_step_ids
            for step in watch_steps
        )
    )

    progress.solve_completed = (
        len(solve_steps) > 0
        and all(
            step.id in completed_step_ids
            for step in solve_steps
        )
    )

    progress.build_completed = (
        len(build_steps) > 0
        and all(
            step.id in completed_step_ids
            for step in build_steps
        )
    )   
    
    # -------------------------
    # COMPREHENSION
    # -------------------------

    accuracy_score = 0.0

    if progress.total_questions > 0:
        accuracy_score = (
            progress.correct_answers
            / progress.total_questions
        )

    # Watch + Solve + Build consistency
    completed_parts = sum([
        progress.watch_completed,
        progress.solve_completed,
        progress.build_completed
    ])

    completion_score = completed_parts / 3

    # Time efficiency
    time_score = 0.0

    if progress.time_spent > 0 and progress.ideal_time > 0:
        ratio = progress.time_spent / progress.ideal_time

        if ratio <= 1:
            time_score = 1.0
        elif ratio <= 1.5:
            time_score = 0.8
        elif ratio <= 2:
            time_score = 0.6
        else:
            time_score = 0.4

    # Build performance
    build_score = progress.build_score

    # Final comprehension
    progress.comprehension_score = round(
        (
            accuracy_score * 0.40
            + build_score * 0.30
            + time_score * 0.15
            + completion_score * 0.15
        ),
        3
    )

    # -------------------------
    # MASTERY
    # -------------------------

    progress.mastery_score = round(
        (
            progress.comprehension_score * 0.70
            + accuracy_score * 0.20
            + build_score * 0.10
        ),
        3
    )

    # A learner cannot demonstrate mastery
    # until all three stages are completed.
    if not (
        progress.watch_completed
        and progress.solve_completed
        and progress.build_completed
    ):
        progress.mastery_score = min(
            progress.mastery_score,
            0.59
        )
    # Mastered only with strong evidence
    if (
        progress.mastery_score >= 0.80
        and accuracy_score >= 0.70
        and build_score >= 0.70
    ):
        progress.needs_revision = False

    elif progress.mastery_score < 0.60:
        progress.needs_revision = True

    db.commit()
    db.refresh(progress)

    return {
        "message": "Interaction recorded",
        "card_id": data.card_id,
        "action": data.action,
        "progress": {
            "time_spent": progress.time_spent,
            "ideal_time": progress.ideal_time,
            "correct_answers": progress.correct_answers,
            "total_questions": progress.total_questions,
            "build_score": progress.build_score,
            "comprehension_score": progress.comprehension_score,
            "mastery_score": progress.mastery_score,
            "needs_revision": progress.needs_revision,
            "watch_completed": progress.watch_completed,
            "solve_completed": progress.solve_completed,
            "build_completed": progress.build_completed
        }
    }