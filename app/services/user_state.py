from sqlalchemy.orm import Session

from ..models import UserSkill, Interaction, Content


def get_or_create_skill(
    db: Session,
    user_id: int,
    skill_name: str
):
    skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill == skill_name
    ).first()

    if not skill:
        skill = UserSkill(
            user_id=user_id,
            skill=skill_name,
            interest_score=0.5,
            skill_score=0.3,
            completion_rate=0.0,
            skip_rate=0.0
        )

        db.add(skill)
        db.commit()
        db.refresh(skill)

    return skill


def update_user_state(
    db: Session,
    interaction: Interaction,
    content: Content
):

    skill = get_or_create_skill(
        db,
        interaction.user_id,
        content.skill
    )

    if interaction.action == "complete":

        skill.completion_rate = min(
            1.0,
            skill.completion_rate * 0.8 + 0.2
        )

        skill.interest_score = min(
            1.0,
            skill.interest_score + 0.03
        )

        skill.skill_score = min(
            1.0,
            skill.skill_score + 0.04
        )

    elif interaction.action == "build" and interaction.completed:

        skill.completion_rate = min(
            1.0,
            max(
                0.0,
                skill.completion_rate * 0.8 + 0.2
            )
        )

        skill.skill_score = min(
            1.0,
            max(
                0.0,
                skill.skill_score + 0.03
            )
        )

        skill.interest_score = min(
            1.0,
            max(
                0.0,
                skill.interest_score + 0.02
            )
        )

    elif interaction.action == "answer":

        skill.completion_rate = min(
            1.0,
            skill.completion_rate * 0.8 + 0.2
        )

        if interaction.correct:

            skill.skill_score = min(
                1.0,
                skill.skill_score + 0.05
            )

            skill.interest_score = min(
                1.0,
                skill.interest_score + 0.02
            )

        else:

            skill.skill_score = max(
                0.0,
                skill.skill_score - 0.02
            )

    elif interaction.action == "skip":

        skill.skip_rate = min(
            1.0,
            skill.skip_rate * 0.8 + 0.2
        )

        skill.interest_score = max(
            0.0,
            skill.interest_score - 0.04
        )

    db.commit()
    db.refresh(skill)

    return skill