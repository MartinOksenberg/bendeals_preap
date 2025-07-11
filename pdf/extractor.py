import fitz  # PyMuPDF
import pdfplumber
import PyPDF2
from pathlib import Path

class PDFTextExtractor:
    """
    Extracts text from a PDF using multiple fallback strategies.
    """
    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)

    def extract_text(self):
        """
        Tries to extract text using PyMuPDF first, then falls back to other methods.
        """
        # Primary Method: PyMuPDF (fitz)
        try:
            text = self.extract_with_pymupdf()
            if text and len(text) > 100:
                print("Successfully extracted text using PyMuPDF.")
                return text
        except Exception as e:
            print(f"PyMuPDF failed: {e}")

        # Fallback 1: pdfplumber
        try:
            text = self.extract_with_pdfplumber()
            if text and len(text) > 100:
                print("Fell back to pdfplumber for text extraction.")
                return text
        except Exception as e:
            print(f"pdfplumber failed: {e}")

        # Fallback 2: PyPDF2
        try:
            text = self.extract_with_pypdf2()
            if text and len(text) > 100:
                print("Fell back to PyPDF2 for text extraction.")
                return text
        except Exception as e:
            print(f"PyPDF2 failed: {e}")

        print("All PDF extraction methods failed.")
        return ""

    def extract_with_pymupdf(self):
        """Extract text using PyMuPDF."""
        text = ""
        with fitz.open(self.pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def extract_with_pdfplumber(self):
        """Extract text using pdfplumber."""
        text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    def extract_with_pypdf2(self):
        """Extract text using PyPDF2."""
        text = ""
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

if __name__ == "__main__":
    import sys
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "PG Sample.pdf"
    extractor = PDFTextExtractor(pdf_file)
    text = extractor.extract_text()
    print(text[:2000])  # Print first 2000 chars for preview
