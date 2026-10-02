import random
import joblib

from pathlib import Path
from sqlalchemy.orm import Session

from ..models import User, UserSkill, Content


# --------------------------------------------------
# Load ML model
# --------------------------------------------------

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "model.pkl"

try:
    model = joblib.load(MODEL_PATH)
    ML_AVAILABLE = True
except Exception:
    model = None
    ML_AVAILABLE = False


# --------------------------------------------------
# Skill state
# --------------------------------------------------

def get_skill_state(
    db: Session,
    user_id: int,
    skill_name: str
):
    return db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill == skill_name
    ).first()


# --------------------------------------------------
# ML completion probability
# --------------------------------------------------

def predict_completion_probability(
    user: User,
    activity: Content,
    skill_state: UserSkill | None
):

    if skill_state:

        interest = skill_state.interest_score
        completion_rate = skill_state.completion_rate
        skip_rate = skill_state.skip_rate

    else:

        # Cold-start defaults
        interest = 0.5
        completion_rate = 0.0
        skip_rate = 0.0


    # Convert user level to number
    level_map = {
        "beginner": 1,
        "intermediate": 2,
        "advanced": 3
    }

    skill_level = level_map.get(
        user.level.lower(),
        1
    )


    # Goal/topic relationship
    topic_match = 0.3

    if user.goal.lower() in activity.topic.lower():
        topic_match = 1.0

    elif activity.topic.lower() in user.goal.lower():
        topic_match = 0.8


    difficulty_gap = abs(
        activity.difficulty - skill_level
    )


    features = [[
        interest,
        skill_level,
        activity.difficulty,
        topic_match,
        completion_rate,
        skip_rate,
        difficulty_gap,
        activity.progress_value
    ]]


    if ML_AVAILABLE:

        probability = model.predict_proba(
            features
        )[0][1]

        return float(probability)


    # --------------------------------------------------
    # Fallback heuristic
    # --------------------------------------------------

    probability = (
        0.35 * interest
        + 0.25 * topic_match
        + 0.20 * completion_rate
        + 0.10 * (1 - skip_rate)
        + 0.10 * max(
            0,
            1 - difficulty_gap * 0.4
        )
    )

    return probability


# --------------------------------------------------
# Recommendation scoring
# --------------------------------------------------

def calculate_recommendation_score(
    user: User,
    activity: Content,
    skill_state: UserSkill | None
):

    completion_probability = (
        predict_completion_probability(
            user,
            activity,
            skill_state
        )
    )


    # Interest
    if skill_state:

        interest_score = (
            skill_state.interest_score
        )

        skip_penalty = (
            skill_state.skip_rate
        )

        skill_score = (
            skill_state.skill_score
        )

    else:

        interest_score = 0.5
        skip_penalty = 0.0
        skill_score = 0.3


    # Progress value
    progress_score = min(
        activity.progress_value / 15,
        1.0
    )


    # Difficulty mismatch
    level_map = {
        "beginner": 1,
        "intermediate": 2,
        "advanced": 3
    }

    expected_difficulty = level_map.get(
        user.level.lower(),
        1
    )

    difficulty_gap = abs(
        activity.difficulty
        - expected_difficulty
    )

    difficulty_penalty = min(
        difficulty_gap / 2,
        1.0
    )


    # Exploration
    exploration = 0.0
    if skill_state is None:
        exploration = 1.0
    else:
        exploration = 0.15


    # --------------------------------------------------
    # Final score
    # --------------------------------------------------
    action_bonus = 0.0

    if activity.type in [
        "coding",
        "simulation",
        "build"
    ]:
        action_bonus = 0.05
    score = (
    0.40 * completion_probability
    + 0.20 * interest_score
    + 0.15 * skill_score
    + 0.15 * progress_score
    + 0.05 * exploration
    + action_bonus
    - 0.10 * skip_penalty
    - 0.10 * difficulty_penalty
    )


    return score


# --------------------------------------------------
# Generate recommendations
# --------------------------------------------------

def recommend_activities(
    db: Session,
    user_id: int,
    limit: int = 5
):

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        return []


    activities = db.query(Content).all()

    scored_activities = []


    for activity in activities:

        skill_state = get_skill_state(
            db,
            user_id,
            activity.skill
        )


        score = calculate_recommendation_score(
            user,
            activity,
            skill_state
        )


        completion_probability = (
            predict_completion_probability(
                user,
                activity,
                skill_state
            )
        )


        scored_activities.append({

            "activity": activity,

            "score": round(
                score,
                4
            ),

            "completion_probability": round(
                completion_probability,
                4
            )

        })


    scored_activities.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    return scored_activities[:limit]


# --------------------------------------------------
# Explain recommendation
# --------------------------------------------------

def get_recommendation_reason(
    user: User,
    activity: Content,
    skill_state: UserSkill | None
):

    reasons = []


    if skill_state and (
        skill_state.interest_score >= 0.6
    ):

        reasons.append(
            f"Matches your "
            f"{activity.skill.replace('_', ' ')} "
            f"interest"
        )


    if skill_state and (
        skill_state.skill_score >= 0.5
    ):

        reasons.append(
            "Builds on a skill "
            "you've already demonstrated"
        )


    if activity.progress_value >= 8:

        reasons.append(
            "High progress value"
        )


    if activity.type in [
        "coding",
        "simulation",
        "build"
    ]:

        reasons.append(
            "Action-based activity"
        )


    if not reasons:

        reasons.append(
            "Recommended to explore "
            "a new skill"
        )


    return reasons