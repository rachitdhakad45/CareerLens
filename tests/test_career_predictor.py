from src.ml.career_predictor import predict_career


def test_career_prediction():

    resume_text = """
    B.Tech Computer Science graduate with experience in data analysis.
    Skilled in Python, SQL, Pandas, NumPy and Tableau.
    Built dashboards and analyzed customer data.
    """

    result = predict_career(resume_text)

    assert result["career_family"]
    assert result["probability"] > 0

    assert len(result["alternatives"]) == 3