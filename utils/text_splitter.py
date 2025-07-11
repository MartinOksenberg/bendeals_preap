import re
from typing import List

def split_by_section_headers(text: str) -> List[str]:
    """
    Splits the input text into chunks based on common credit report section headers.
    Returns a list of text chunks, each starting with a detected header.
    """
    # Common section headers (add more as needed)
    headers = [
        r"INQUIRIES", r"ACCOUNTS", r"REVOLVING ACCOUNTS", r"CREDIT CARDS", r"CHARGE ACCOUNTS",
        r"INSTALLMENT LOANS", r"MORTGAGES", r"NEGATIVE ITEMS", r"COLLECTIONS", r"SUMMARY", r"PUBLIC RECORDS"
    ]
    # Build regex pattern for headers (case-insensitive, at line start)
    pattern = re.compile(rf"^({'|'.join(headers)})", re.IGNORECASE | re.MULTILINE)
    # Find all header positions
    matches = list(pattern.finditer(text))
    if not matches:
        return [text]
    # Split text at header positions
    chunks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
    return chunks
