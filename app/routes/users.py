from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, LearningPreferences
from ..schemas import UserCreate, UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "/",
    response_model=UserResponse
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    user = User(
        name=user_data.name,
        goal=user_data.goal,
        level=user_data.level,
        learning_style=user_data.learning_style
    )

    db.add(user)
    db.flush()

    # -----------------------------------------
    # Create adaptive learning preferences
    # -----------------------------------------

    style = user_data.learning_style.lower()

    if style == "watch":
        preferences = LearningPreferences(
            user_id=user.id,
            watch_weight=0.50,
            solve_weight=0.20,
            build_weight=0.20,
            explore_weight=0.10
        )

    elif style == "solve":
        preferences = LearningPreferences(
            user_id=user.id,
            watch_weight=0.20,
            solve_weight=0.50,
            build_weight=0.20,
            explore_weight=0.10
        )

    elif style == "build":
        preferences = LearningPreferences(
            user_id=user.id,
            watch_weight=0.20,
            solve_weight=0.20,
            build_weight=0.50,
            explore_weight=0.10
        )

    else:
        preferences = LearningPreferences(
            user_id=user.id,
            watch_weight=0.25,
            solve_weight=0.25,
            build_weight=0.25,
            explore_weight=0.25
        )

    db.add(preferences)

    db.commit()
    db.refresh(user)

    return user
