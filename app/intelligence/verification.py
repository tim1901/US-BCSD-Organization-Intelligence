class VerificationService:
    def verify(self, claim: str, sources: list[dict]) -> dict:
        return {'claim':claim,'status':'unverified' if not sources else 'candidate','sources':sources}
