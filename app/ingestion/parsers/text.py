from .base import DocumentParser
class TextParser(DocumentParser):
    def supports(self, filename, content_type=None):
        return filename.lower().endswith(('.txt', '.text')) or content_type in {'text/plain'}
    def parse(self, data, filename):
        return data.decode('utf-8', errors='replace'), {'parser':'text'}
