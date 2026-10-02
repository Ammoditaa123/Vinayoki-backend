import json
from pathlib import Path

from app.database import SessionLocal
from app.models import Content


def load_content():
    db = SessionLocal()

    try:
        content_path = Path(__file__).resolve().parent.parent / "data" / "content.json"

        print(f"Loading content from: {content_path}")

        if not content_path.exists():
            print(f"ERROR: content.json not found at {content_path}")
            return

        with open(content_path, "r", encoding="utf-8") as file:
            content_data = json.load(file)

        existing_count = db.query(Content).count()

        if existing_count > 0:
            print(f"Content already exists: {existing_count} activities.")
            return

        for item in content_data:
            content = Content(**item)
            db.add(content)

        db.commit()

        print(f"Loaded {len(content_data)} activities successfully.")

    except Exception as e:
        db.rollback()
        print(f"ERROR loading content: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    load_content()