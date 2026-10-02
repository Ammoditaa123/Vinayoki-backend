from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
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
    db.commit()
    db.refresh(user)

    return user