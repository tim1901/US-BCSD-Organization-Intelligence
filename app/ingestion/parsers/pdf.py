import fitz
from .base import DocumentParser

class PdfParser(DocumentParser):
    def supports(self, filename, content_type=None):
        return filename.lower().endswith('.pdf') or content_type == 'application/pdf'

    def parse(self, data, filename):
        doc = fitz.open(stream=data, filetype='pdf')
        parts = []
        for i, page in enumerate(doc):
            parts.append(f"\n[Page {i+1}]\n{page.get_text()}")
        return "\n".join(parts), {'parser': 'pdf', 'pages': len(doc)}
