HIERARCHY = {
    'government':6, 'regulator':6, 'legal_primary':6,
    'official_company':5, 'institutional':5,
    'academic':4, 'research':4,
    'industry':3, 'major_media':2, 'secondary':1,
}
class SourceQuality:
    def score(self, source_type: str) -> int: return HIERARCHY.get(source_type, 0)
