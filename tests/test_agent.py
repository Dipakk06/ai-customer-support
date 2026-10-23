from app.agent import answer_customer
from app.db import init_db

def test_order_lookup():
    init_db()
    result = answer_customer("Where is order ORD-1001?")
    assert "ORD-1001" in result["answer"]
    assert result["intent"] == "order"

def test_ticket_creation():
    result = answer_customer("My product arrived damaged.")
    assert "TKT-" in result["answer"]
    assert result["intent"] == "ticket"

def test_faq():
    result = answer_customer("What is your return policy?")
    assert result["intent"] == "faq"
    assert "return" in result["answer"].lower()
