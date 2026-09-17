from app.ingestion.parsers.text import TextParser

def test_text_parser():
    text, meta=TextParser().parse(b'hello', 'x.txt')
    assert text=='hello'; assert meta['parser']=='text'
