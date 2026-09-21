from app.brain.intent import IntentResolver


def test_competitive_questions_trigger_competitive_analysis():
    resolver = IntentResolver()

    assert resolver.resolve("Who are US BCSD's competitors?")["intent"] == "competitive_analysis"
    assert resolver.resolve("What organizations are similar to US BCSD?")["intent"] == "competitive_analysis"
    assert resolver.resolve("Who are the main peers in this market?")["intent"] == "competitive_analysis"


def test_normal_organizational_questions_do_not_trigger_web_research():
    resolver = IntentResolver()

    assert resolver.resolve("What did we discuss about the annual meeting?")["intent"] == "meeting_preparation"
    assert resolver.resolve("What are US BCSD's main areas of work?")["intent"] == "organizational_question"
