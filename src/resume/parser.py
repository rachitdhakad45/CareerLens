from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract readable text from a PDF resume.

    Args:
        pdf_file: PDF file path or file-like object.

    Returns:
        Extracted resume text.

    Raises:
        ValueError: If the PDF cannot be read or contains no extractable text.
    """

    try:
        reader = PdfReader(pdf_file)

        if not reader.pages:
            raise ValueError("The PDF contains no pages.")

        extracted_text = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                extracted_text.append(text)

        final_text = "\n".join(extracted_text).strip()

        if not final_text:
            raise ValueError(
                "No readable text was found in the PDF. "
                "The resume may be image-based or scanned."
            )

        return final_text

    except PdfReadError as error:
        raise ValueError(
            "The uploaded file is not a valid or readable PDF."
        ) from error