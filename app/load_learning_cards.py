import json
from pathlib import Path

from app.database import SessionLocal
from app.models import LearningCard, LearningStep


def load_learning_cards():
    db = SessionLocal()

    try:
        cards_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "learning_cards.json"
        )

        print(f"Loading learning cards from: {cards_path}")

        if not cards_path.exists():
            print(
                f"ERROR: learning_cards.json not found at {cards_path}"
            )
            return

        with open(
            cards_path,
            "r",
            encoding="utf-8"
        ) as file:
            cards_data = json.load(file)

        existing_count = db.query(LearningCard).count()

        if existing_count > 0:
            print(
                f"Learning cards already exist: "
                f"{existing_count} cards."
            )
            return

        total_steps = 0

        for card_data in cards_data:
            steps_data = card_data.pop("steps", [])

            card = LearningCard(**card_data)

            db.add(card)
            db.flush()

            for step_data in steps_data:
                step = LearningStep(
                    card_id=card.id,
                    **step_data
                )

                db.add(step)
                total_steps += 1

        db.commit()

        print(
            f"Loaded {len(cards_data)} learning cards "
            f"with {total_steps} learning steps."
        )

    except Exception as e:
        db.rollback()

        print(
            f"ERROR loading learning cards: {e}"
        )

        raise

    finally:
        db.close()


if __name__ == "__main__":
    load_learning_cards()