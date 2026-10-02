from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Content, Interaction
from ..schemas import InteractionCreate, InteractionResponse
from ..services.user_state import update_user_state


router = APIRouter(
    prefix="/interactions",
    tags=["Interactions"]
)


@router.post(
    "/",
    response_model=InteractionResponse
)
def create_interaction(
    interaction_data: InteractionCreate,
    db: Session = Depends(get_db)
):

    # 1. Check whether this request was already processed
    existing = db.query(Interaction).filter(
        Interaction.idempotency_key
        == interaction_data.idempotency_key
    ).first()

    if existing:
        return existing

    # 2. Check that user exists
    user = db.query(User).filter(
        User.id == interaction_data.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 3. Check that content exists
    content = db.query(Content).filter(
        Content.id == interaction_data.content_id
    ).first()

    if not content:
        raise HTTPException(
            status_code=404,
            detail="Content not found"
        )

    # 4. Calculate progress earned
    progress_earned = 0

    if interaction_data.action == "view":
        progress_earned = 0

    elif interaction_data.action == "skip":
        progress_earned = 0

    elif interaction_data.action == "answer":
        progress_earned = 3

        if interaction_data.correct:
            progress_earned = 5

    elif interaction_data.action == "complete":
        progress_earned = content.progress_value

    elif interaction_data.action == "build":
        progress_earned = content.progress_value

    # 5. Create interaction
    interaction = Interaction(
        user_id=interaction_data.user_id,
        content_id=interaction_data.content_id,
        action=interaction_data.action,
        time_spent=interaction_data.time_spent,
        correct=interaction_data.correct,
        completed=interaction_data.completed,
        progress_earned=progress_earned,
        idempotency_key=interaction_data.idempotency_key
    )

    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    update_user_state(
        db,
        interaction,
        content
    )

    return interaction