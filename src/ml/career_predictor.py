from pathlib import Path
import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = PROJECT_ROOT / "models"

VECTORIZER_PATH = MODEL_DIR / "career_vectorizer.joblib"
CLASSIFIER_PATH = MODEL_DIR / "career_classifier.joblib"


def load_career_model():
    """
    Load the trained TF-IDF vectorizer
    and career-family classifier.
    """

    if not VECTORIZER_PATH.exists():
        raise FileNotFoundError(
            f"Career vectorizer not found: {VECTORIZER_PATH}"
        )

    if not CLASSIFIER_PATH.exists():
        raise FileNotFoundError(
            f"Career classifier not found: {CLASSIFIER_PATH}"
        )

    vectorizer = joblib.load(VECTORIZER_PATH)
    classifier = joblib.load(CLASSIFIER_PATH)

    return vectorizer, classifier


def predict_career(resume_text: str, top_n: int = 3):
    """
    Predict the most likely career families
    for a resume.
    """

    if not resume_text or not resume_text.strip():
        raise ValueError(
            "Resume text cannot be empty."
        )

    vectorizer, classifier = load_career_model()

    resume_vector = vectorizer.transform(
        [resume_text]
    )

    probabilities = classifier.predict_proba(
        resume_vector
    )[0]

    ranking = probabilities.argsort()[::-1]

    predictions = []

    for index in ranking[:top_n]:

        predictions.append({
            "career_family": classifier.classes_[index],
            "probability": float(
                probabilities[index]
            )
        })

    return {
        "career_family": predictions[0]["career_family"],
        "probability": predictions[0]["probability"],
        "alternatives": predictions
    }