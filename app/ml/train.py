import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score


FEATURES = [
    "user_interest",
    "skill_level",
    "content_difficulty",
    "content_topic_match",
    "previous_completion_rate",
    "previous_skip_rate",
    "difficulty_gap",
    "progress_value",
    "mastery_score",
    "accuracy_score",
    "time_efficiency",
    "build_score",
    "attempt_count"
]

# Load dataset
df = pd.read_csv("data/interactions.csv")

X = df[FEATURES]
y = df["completed"]


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# ML pipeline
model = Pipeline([
    (
        "scaler",
        StandardScaler()
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000,
            random_state=42
        )
    )
])


# Train
model.fit(X_train, y_train)


# Predictions
predictions = model.predict(X_test)

probabilities = model.predict_proba(X_test)[:, 1]


# Evaluation
accuracy = accuracy_score(
    y_test,
    predictions
)

roc_auc = roc_auc_score(
    y_test,
    probabilities
)


print("=" * 50)
print("VINAYOKI ML MODEL")
print("=" * 50)

print(f"Training samples: {len(X_train)}")
print(f"Testing samples:  {len(X_test)}")

print(f"\nAccuracy: {accuracy:.4f}")
print(f"ROC-AUC:  {roc_auc:.4f}")


# Save model
joblib.dump(
    model,
    "app/ml/model.pkl"
)

print("\nModel saved to:")
print("app/ml/model.pkl")