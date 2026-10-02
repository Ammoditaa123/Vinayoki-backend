from sqlalchemy.orm import Session

from ..models import Interaction


MEANINGFUL_ACTIONS = [
    "answer",
    "complete",
    "build"
]


def detect_passive_consumption(
    db: Session,
    user_id: int
):

    recent_interactions = (
        db.query(Interaction)
        .filter(
            Interaction.user_id == user_id
        )
        .order_by(
            Interaction.timestamp.desc()
        )
        .limit(10)
        .all()
    )


    if len(recent_interactions) < 5:
        return {
            "intervention": False,
            "recent_views": 0,
            "meaningful_actions": 0
        }


    recent_views = sum(
        1
        for interaction in recent_interactions
        if interaction.action == "view"
    )


    meaningful_actions = sum(
        1
        for interaction in recent_interactions
        if interaction.action in MEANINGFUL_ACTIONS
    )


    intervention = (
        recent_views >= 5
        and meaningful_actions == 0
    )


    return {
        "intervention": intervention,
        "recent_views": recent_views,
        "meaningful_actions": meaningful_actions
    }