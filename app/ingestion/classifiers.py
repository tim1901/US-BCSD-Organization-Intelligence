from pathlib import Path

def classify_filename(name: str) -> str:
    ext = Path(name).suffix.lower()
    return {
        '.txt':'text', '.md':'markdown', '.pdf':'pdf', '.docx':'docx', '.pptx':'pptx', '.xlsx':'xlsx',
        '.html':'html', '.htm':'html'
    }.get(ext, 'unknown')
