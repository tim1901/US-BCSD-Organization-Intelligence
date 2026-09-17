from bs4 import BeautifulSoup
from .base import DocumentParser

class HtmlParser(DocumentParser):
    def supports(self, filename, content_type=None):
        return filename.lower().endswith(('.html', '.htm')) or content_type == 'text/html'

    def parse(self, data, filename):
        soup = BeautifulSoup(data, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        return soup.get_text("\n"), {'parser': 'html'}
