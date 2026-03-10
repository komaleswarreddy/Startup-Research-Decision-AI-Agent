from app.agents.intent_router import IntentRouter


def test_intent_router_accepts_startup_queries() -> None:
    router = IntentRouter()
    result = router.classify("Analyze Indian EV startups and rank investment opportunities")
    assert result.in_scope is True
    assert result.route in {"startup_investment", "market_analysis", "startup_comparison"}


def test_intent_router_routes_startup_creation_queries() -> None:
    router = IntentRouter()
    result = router.classify("How to start a startup in India with legal steps")
    assert result.in_scope is True
    assert result.route == "startup_creation"


def test_intent_router_rejects_general_knowledge_queries() -> None:
    router = IntentRouter()
    result = router.classify("who is cm of ap")
    assert result.in_scope is False
    assert result.route == "out_of_scope"


def test_intent_router_rejects_greeting_and_self_intro() -> None:
    router = IntentRouter()
    greeting = router.classify("hi")
    intro = router.classify("my name is komal")
    assert greeting.in_scope is False
    assert intro.in_scope is False


def test_intent_router_rejects_empty_query() -> None:
    router = IntentRouter()
    result = router.classify("   ")
    assert result.in_scope is False
    assert "Empty or invalid query" in result.reason
