from sqlalchemy.orm import Session

import joblib
import pandas as pd

from pathlib import Path

from ..ml.features import build_card_features
from ..models import (
    LearningCard,
    CardProgress,
    User,
    UserSkill,
    LearningPreferences
)

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "ml"
    / "model.pkl"
)


def predict_completion_probability(features):
    model = joblib.load(MODEL_PATH)

    model_features = {
        "user_interest": features["user_interest"],
        "skill_level": features["skill_level"],
        "content_difficulty": features["content_difficulty"],
        "content_topic_match": features["content_topic_match"],
        "previous_completion_rate": features[
            "previous_completion_rate"
        ],
        "previous_skip_rate": features[
            "previous_skip_rate"
        ],
        "difficulty_gap": features["difficulty_gap"],
        "progress_value": features["progress_value"]
    }

    X = pd.DataFrame([model_features])

    return float(
        model.predict_proba(X)[0][1]
    )

def get_card_recommendations(
    db: Session,
    user_id: int,
    limit: int = 5
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return []

    cards = db.query(LearningCard).all()

    # ------------------------------------------------
    # Get learner's preferred activity weights
    # ------------------------------------------------

    preferences = (
        db.query(LearningPreferences)
        .filter(
            LearningPreferences.user_id == user_id
        )
        .first()
    )

    # Safe fallback for older users
    if not preferences:
        preferences = LearningPreferences(
            user_id=user_id,
            watch_weight=0.25,
            solve_weight=0.25,
            build_weight=0.25,
            explore_weight=0.25
        )

    results = []

    for card in cards:

        progress = (
            db.query(CardProgress)
            .filter(
                CardProgress.user_id == user_id,
                CardProgress.card_id == card.id
            )
            .first()
        )

        skill_state = (
            db.query(UserSkill)
            .filter(
                UserSkill.user_id == user_id,
                UserSkill.skill == card.skill
            )
            .first()
        )

        # ------------------------------------------------
        # 1. Never recommend mastered cards normally
        # ------------------------------------------------

        if progress and (
            progress.mastery_score >= 0.80
            and not progress.needs_revision
        ):
            continue

        # ------------------------------------------------
        # 2. Build ML features
        # ------------------------------------------------

        features = build_card_features(
            db,
            user_id,
            card
        )

        if features is None:
            continue

        # ------------------------------------------------
        # 3. Cold-start ML prediction
        # ------------------------------------------------

        completion_probability = (
            predict_completion_probability(features)
        )

        # ------------------------------------------------
        # 4. Real learner performance
        # ------------------------------------------------

        performance_score = (
            0.40 * features["mastery_score"]
            + 0.25 * features["accuracy_score"]
            + 0.20 * features["build_score"]
            + 0.15 * features["time_efficiency"]
        )

        # ------------------------------------------------
        # 5. Interest
        # ------------------------------------------------

        if skill_state:
            interest_score = skill_state.interest_score
        else:
            interest_score = 0.5  # Neutral exploration value

        # ------------------------------------------------
        # 6. Existing skill
        # ------------------------------------------------

        if skill_state:
            skill_fit_score = skill_state.skill_score
        else:
            skill_fit_score = 0.5  # Neutral default

        # ------------------------------------------------
        # 7. Progress value
        # ------------------------------------------------

        progress_score = min(
            card.progress_value / 15.0,
            1.0
        )

        # ------------------------------------------------
        # 8. Activity preference
        # ------------------------------------------------

        step_types = [
            step.type
            for step in card.steps
        ]

        watch_ratio = (
            step_types.count("watch") / len(step_types)
            if step_types
            else 0
        )

        solve_ratio = (
            step_types.count("solve") / len(step_types)
            if step_types
            else 0
        )

        build_ratio = (
            step_types.count("build") / len(step_types)
            if step_types
            else 0
        )

        preference_score = (
            watch_ratio * preferences.watch_weight
            + solve_ratio * preferences.solve_weight
            + build_ratio * preferences.build_weight
        )

        # ------------------------------------------------
        # BASE SCORE CALCULATION
        # ------------------------------------------------

        score = (
            0.40 * completion_probability
            + 0.30 * performance_score
            + 0.10 * interest_score
            + 0.05 * skill_fit_score
            + 0.05 * progress_score
            + 0.10 * preference_score
        )

        # ------------------------------------------------
        # ADAPTIVE ADJUSTMENTS
        # ------------------------------------------------

        # Revision/practice
        if progress:
            if progress.mastery_score < 0.60:
                score += 0.05
            elif progress.mastery_score < 0.80:
                score += 0.025

            if progress.needs_revision:
                score += 0.05

        # Difficulty adaptation
        if skill_state:
            skill_level = skill_state.skill_score

            if skill_level < 0.40:
                preferred_difficulty = 1
            elif skill_level < 0.70:
                preferred_difficulty = 2
            else:
                preferred_difficulty = 3

            difficulty_gap = abs(
                card.difficulty - preferred_difficulty
            )

            score -= 0.025 * difficulty_gap

        # ------------------------------------------------
        # Keep score bounded
        # ------------------------------------------------

        score = max(0.0, min(score, 1.0))

        results.append({
            "card": card,
            "score": round(score, 4),
            "completion_probability": round(completion_probability, 4),
            "performance_score": round(performance_score, 4),
            "interest_score": round(interest_score, 4),
            "skill_fit_score": round(skill_fit_score, 4),
            "progress_score": round(progress_score, 4),
            "preference_score": round(preference_score, 4)
        })

    # ------------------------------------------------
    # Highest adaptive scores first
    # ------------------------------------------------

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:limit]