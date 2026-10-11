from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "career_model_training_data.csv"
MODEL_DIR = PROJECT_ROOT / "models"

MODEL_DIR.mkdir(exist_ok=True)


# Load dataset using built-in csv module
import csv

with DATA_PATH.open("r", encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))


resume_texts = [row["resume_text"] for row in rows]
career_families = [row["career_family"] for row in rows]


print(f"Total records: {len(rows)}")
print(f"Unique career families: {len(set(career_families))}")


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    resume_texts,
    career_families,
    test_size=0.20,
    random_state=42,
    stratify=career_families,
)


# TF-IDF
vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
)

X_train_tfidf = vectorizer.fit_transform(X_train)


print(f"Training samples: {len(X_train)}")
print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")


# Logistic Regression
classifier = LogisticRegression(
    max_iter=2000,
    class_weight="balanced",
    random_state=42,
)

classifier.fit(X_train_tfidf, y_train)


# Save artifacts
vectorizer_path = MODEL_DIR / "career_vectorizer.joblib"
classifier_path = MODEL_DIR / "career_classifier.joblib"

joblib.dump(vectorizer, vectorizer_path)
joblib.dump(classifier, classifier_path)


print()
print("Model training complete.")
print(f"Vectorizer saved: {vectorizer_path}")
print(f"Classifier saved: {classifier_path}")