from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..ml.features import build_card_features
from ..models import (
    CardProgress,
    LearningCard,
    RecommendationHistory,
    User,
)
from ..services.card_recommender import (
    get_card_recommendations,
    predict_completion_probability,
)


router = APIRouter(tags=["Adaptation Snapshot"])


@router.get("/adaptation/{user_id}/{card_id}")
def get_adaptation_snapshot(
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

    # Query progress directly. In particular, do not call GET /cards/{card_id},
    # which creates a CardProgress row when one does not exist.
    progress = (
        db.query(CardProgress)
        .filter(
            CardProgress.user_id == user_id,
            CardProgress.card_id == card_id,
        )
        .first()
    )

    features = build_card_features(db, user_id, card)
    if features is None:
        raise HTTPException(status_code=404, detail="User not found")

    completion_probability = predict_completion_probability(features)

    # get_card_recommendations is the existing read-only scoring pipeline.
    # Request its full candidate set so a selected card can be matched even
    # when it falls outside the normal feed's top five.
    card_count = db.query(LearningCard).count()
    recommendations = get_card_recommendations(
        db,
        user_id,
        limit=card_count,
    )
    recommendation = next(
        (
            item
            for item in recommendations
            if item["card"].id == card_id
        ),
        None,
    )

    latest_history = (
        db.query(RecommendationHistory)
        .filter(
            RecommendationHistory.user_id == user_id,
            RecommendationHistory.card_id == card_id,
        )
        .order_by(
            RecommendationHistory.created_at.desc(),
            RecommendationHistory.id.desc(),
        )
        .first()
    )

    if progress is None:
        learner_state = {
            "mastery_score": 0.0,
            "accuracy_score": 0.0,
            "build_score": 0.0,
            "time_efficiency": 0.0,
            "attempt_count": 0,
        }
    else:
        learner_state = {
            "mastery_score": features["mastery_score"],
            "accuracy_score": features["accuracy_score"],
            "build_score": features["build_score"],
            "time_efficiency": features["time_efficiency"],
            "attempt_count": features["attempt_count"],
        }

    return {
        "user_id": user_id,
        "card_id": card_id,
        "learner_state": learner_state,
        "ml": {
            "completion_probability": completion_probability,
        },
        "recommendation": {
            "recommendation_score": (
                recommendation["score"] if recommendation else None
            ),
            "rank": latest_history.rank if latest_history else None,
        },
    }
