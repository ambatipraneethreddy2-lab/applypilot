"""Turn an uploaded resume file into plain text."""
import io
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_BYTES = 5 * 1024 * 1024  # 5 MB


class ResumeParseError(ValueError):
    pass


def extract_text(filename: str, data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise ResumeParseError("File is too large (max 5 MB).")
    name = filename.lower()
    if name.endswith(".pdf") or data[:4] == b"%PDF":
        try:
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except (PdfReadError, Exception) as e:  # pypdf raises several error types on bad files
            raise ResumeParseError("Could not read this PDF.") from e
    elif name.endswith((".txt", ".md")):
        text = data.decode("utf-8", errors="ignore")
    else:
        raise ResumeParseError("Please upload a PDF or .txt file.")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < 100:
        # Usually a scanned (image-only) PDF: there is no text layer to read.
        raise ResumeParseError("Couldn't find enough text. If your resume is a scanned image, export it as a text PDF.")
    return text
