import json

from app.database import SessionLocal
from app.models import Content


def load_content():
    db = SessionLocal()

    try:
        with open("data/content.json", "r") as file:
            content_data = json.load(file)

        existing_count = db.query(Content).count()

        if existing_count > 0:
            print("Content already exists.")
            return

        for item in content_data:
            content = Content(**item)
            db.add(content)

        db.commit()

        print(f"Loaded {len(content_data)} activities successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    load_content()