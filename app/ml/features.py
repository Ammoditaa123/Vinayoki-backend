from sqlalchemy.orm import Session

from ..models import (
    User,
    UserSkill,
    LearningCard,
    CardProgress
)


def build_card_features(
    db: Session,
    user_id: int,
    card: LearningCard
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return None

    skill_state = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.skill == card.skill
        )
        .first()
    )

    progress = (
        db.query(CardProgress)
        .filter(
            CardProgress.user_id == user_id,
            CardProgress.card_id == card.id
        )
        .first()
    )

    user_interest = (
        skill_state.interest_score
        if skill_state
        else 0.5
    )

    skill_level = (
        skill_state.skill_score
        if skill_state
        else 0.3
    )

    previous_completion_rate = (
        skill_state.completion_rate
        if skill_state
        else 0.0
    )

    previous_skip_rate = (
        skill_state.skip_rate
        if skill_state
        else 0.0
    )

    if skill_level < 0.40:
        expected_difficulty = 1
    elif skill_level < 0.70:
        expected_difficulty = 2
    else:
        expected_difficulty = 3

    difficulty_gap = abs(
        card.difficulty - expected_difficulty
    )

    if progress:
        accuracy_score = (
            progress.correct_answers /
            progress.total_questions
            if progress.total_questions > 0
            else 0.0
        )

        if progress.time_spent > 0 and progress.ideal_time > 0:
            ratio = (
                progress.time_spent /
                progress.ideal_time
            )

            if ratio <= 1:
                time_efficiency = 1.0
            elif ratio <= 1.5:
                time_efficiency = 0.8
            elif ratio <= 2:
                time_efficiency = 0.6
            else:
                time_efficiency = 0.4
        else:
            time_efficiency = 0.0

        mastery_score = progress.mastery_score
        build_score = progress.build_score
        attempt_count = progress.attempt_count

    else:
        accuracy_score = 0.0
        time_efficiency = 0.0
        mastery_score = 0.0
        build_score = 0.0
        attempt_count = 0

    return {
        "user_interest": user_interest,
        "skill_level": skill_level,
        "content_difficulty": card.difficulty,
        "content_topic_match": user_interest,
        "previous_completion_rate": previous_completion_rate,
        "previous_skip_rate": previous_skip_rate,
        "difficulty_gap": difficulty_gap,
        "progress_value": card.progress_value,

        "mastery_score": mastery_score,
        "accuracy_score": accuracy_score,
        "time_efficiency": time_efficiency,
        "build_score": build_score,
        "attempt_count": attempt_count
    }