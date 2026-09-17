class ClaimExtractor:
    def extract(self, text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()][:50]
