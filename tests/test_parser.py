from src.resume.parser import extract_text_from_pdf


def test_parser_import():
    assert callable(extract_text_from_pdf)