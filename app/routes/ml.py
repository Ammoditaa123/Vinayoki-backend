import joblib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..ml.features import build_card_features
from ..models import LearningCard, User
from ..services.card_recommender import (
    MODEL_PATH,
    predict_completion_probability,
)


router = APIRouter(prefix="/ml", tags=["ML Transparency"])


@router.get("/prediction/{user_id}/{card_id}")
def get_completion_prediction(
    user_id: int,
    card_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    card = db.query(LearningCard).filter(LearningCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    features = build_card_features(db, user_id, card)
    if features is None:
        raise HTTPException(status_code=404, detail="User not found")

    model = joblib.load(MODEL_PATH)
    feature_names = list(model.feature_names_in_)
    model_features = {
        name: features[name]
        for name in feature_names
    }
    adaptive_features = {
        name: value
        for name, value in features.items()
        if name not in feature_names
    }

    completion_probability = predict_completion_probability(features)

    pipeline_steps = getattr(model, "named_steps", {})
    model_type = "Pipeline"
    if pipeline_steps:
        model_type = "Pipeline(" + ", ".join(
            type(step).__name__
            for step in pipeline_steps.values()
        ) + ")"

    return {
        "user_id": user_id,
        "card_id": card_id,
        "features": {
            "model_features": model_features,
            "adaptive_features": adaptive_features,
        },
        "prediction": {
            "completion_probability": completion_probability,
        },
        "model": {
            "type": model_type,
            "feature_count": int(model.n_features_in_),
            "feature_names": feature_names,
        },
    }
