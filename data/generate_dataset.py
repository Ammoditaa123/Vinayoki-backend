import random
import pandas as pd

random.seed(42)

rows = []

for _ in range(5000):

    # Simulated user state
    user_interest = random.uniform(0.1, 1.0)

    skill_level = random.choice([1, 2, 3])

    previous_completion_rate = random.uniform(0.0, 1.0)
    previous_skip_rate = random.uniform(0.0, 0.7)

    # Simulated activity
    content_difficulty = random.choice([1, 2, 3])

    content_topic_match = random.uniform(0.0, 1.0)

    progress_value = random.choice([
        3, 4, 5, 6, 7, 8, 9, 10, 15
    ])

    difficulty_gap = abs(
        content_difficulty - skill_level
    )

    # -----------------------------------------
    # Simulate probability of meaningful completion
    # -----------------------------------------

    score = (
        1.8 * user_interest
        + 1.2 * content_topic_match
        + 1.0 * previous_completion_rate
        - 1.4 * previous_skip_rate
        - 0.9 * difficulty_gap
        + 0.04 * progress_value
    )

    probability = 1 / (1 + pow(2.71828, -score + 2.0))

    completed = 1 if random.random() < probability else 0

    rows.append({
        "user_interest": round(user_interest, 3),
        "skill_level": skill_level,
        "content_difficulty": content_difficulty,
        "content_topic_match": round(content_topic_match, 3),
        "previous_completion_rate": round(
            previous_completion_rate, 3
        ),
        "previous_skip_rate": round(
            previous_skip_rate, 3
        ),
        "difficulty_gap": difficulty_gap,
        "progress_value": progress_value,
        "completed": completed
    })


df = pd.DataFrame(rows)

df.to_csv(
    "data/interactions.csv",
    index=False
)

print("Dataset generated successfully.")
print("Rows:", len(df))
print("\nCompletion distribution:")
print(df["completed"].value_counts())

print("\nFirst 5 rows:")
print(df.head())