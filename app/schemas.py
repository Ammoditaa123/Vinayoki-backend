from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    name: str
    goal: str
    level: str
    learning_style: str


class UserResponse(BaseModel):
    id: int
    name: str
    goal: str
    level: str
    learning_style: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InteractionCreate(BaseModel):
    user_id: int
    content_id: int
    action: str
    time_spent: int = 0
    correct: bool | None = None
    completed: bool = False
    idempotency_key: str


class InteractionResponse(BaseModel):
    id: int
    user_id: int
    content_id: int
    action: str
    time_spent: int
    correct: bool | None
    completed: bool
    progress_earned: float
    idempotency_key: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)