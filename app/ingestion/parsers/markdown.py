from .base import DocumentParser
class MarkdownParser(DocumentParser):
    def supports(self, filename, content_type=None):
        return filename.lower().endswith('.md')
    def parse(self, data, filename):
        return data.decode('utf-8', errors='replace'), {'parser':'markdown'}
