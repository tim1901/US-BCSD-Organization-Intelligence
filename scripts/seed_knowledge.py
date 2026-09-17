from pathlib import Path
from app.core.ids import sha256_text

def main():
    path=Path('knowledge/seed/us_bcsd_seed_knowledge.md')
    text=path.read_text(encoding='utf-8')
    print({'source':'seed','sha256':sha256_text(text),'bytes':len(text.encode())})
    print('Next step: write this source through the ingestion -> extraction -> memory pipeline.')
if __name__=='__main__': main()
