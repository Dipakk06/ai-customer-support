
import re
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.config import GROQ_API_KEY, MODEL_NAME
from app.knowledge import search_faqs
from app.orders import lookup_order
from app.db import create_ticket


# --------------------------------------------------
# State
# --------------------------------------------------
class SupportState(TypedDict, total=False):
    message: str
    customer_name: str
    answer: str
    intent: str
    tool_result: str


# --------------------------------------------------
# Intent detection
# --------------------------------------------------
def _intent(message: str) -> str:
    m = message.lower().strip()

    # Greetings
    if re.fullmatch(
        r"(hi+|hello+|hey+|hii+|helo+|howdy|"
        r"good morning|good afternoon|good evening)"
        r"[!.?,\s]*",
        m,
    ):
        return "greeting"

    # Existing ticket lookup
    if re.search(r"\bTKT-\d+\b", message, re.IGNORECASE):
        return "ticket_lookup"

    # Human escalation
    if any(
        phrase in m
        for phrase in (
            "human",
            "agent",
            "representative",
            "manager",
            "real person",
            "speak to someone",
            "talk to someone",
            "speak to a person",
            "talk to a person",
            "escalate",
        )
    ):
        return "escalate"

    # Order lookup
    if (
        re.search(r"\bORD-\d+\b", message, re.IGNORECASE)
        or any(
            phrase in m
            for phrase in (
                "order",
                "delivery",
                "tracking",
                "shipped",
                "where is",
            )
        )
    ):
        return "order"

    # Support issues
    if any(
        phrase in m
        for phrase in (
            "create a ticket",
            "raise a ticket",
            "open a ticket",
            "complaint",
            "damaged",
            "broken",
            "refund",
            "charged twice",
            "double charge",
            "duplicate charge",
            "payment failed",
            "payment issue",
            "not working",
            "issue",
            "problem",
            "wrong item",
            "missing item",
        )
    ):
        return "ticket"

    return "faq"


# --------------------------------------------------
# Extract order ID
# --------------------------------------------------
def _extract_order_id(message: str) -> str | None:
    match = re.search(r"\bORD-\d+\b", message, re.IGNORECASE)
    return match.group(0).upper() if match else None


# --------------------------------------------------
# Run tools based on intent
# --------------------------------------------------
def _run_tool(state: SupportState) -> SupportState:
    message = state["message"].strip()
    intent = _intent(message)

    name = (
        state.get("customer_name", "Demo Customer").strip()
        or "Demo Customer"
    )

    # 1. Greeting
    if intent == "greeting":
        return {
            "intent": intent,
            "tool_result": (
                "Hi there! 👋 Welcome to AI Customer Support. "
                "How can I help you today?"
            ),
        }

    # 2. Order lookup
    if intent == "order":
        order_id = _extract_order_id(message)

        if not order_id:
            result = (
                "Please share your order ID, for example ORD-1001, "
                "so I can check its status."
            )
        else:
            try:
                result = str(lookup_order(order_id))
            except Exception:
                result = (
                    "I couldn't retrieve that order right now. "
                    "Please verify your order ID or contact support."
                )

        return {
            "intent": intent,
            "tool_result": result,
        }

    # 3. Existing ticket lookup
    if intent == "ticket_lookup":
        # Ticket retrieval is not implemented in the supplied
        # database interface. Do not pretend to look it up.
        ticket_id = re.search(
            r"\bTKT-\d+\b",
            message,
            re.IGNORECASE,
        ).group(0).upper()

        return {
            "intent": intent,
            "tool_result": (
                f"You provided ticket {ticket_id}. "
                "Ticket status lookup is not configured yet. "
                "Please contact the support team to verify its status."
            ),
        }

    # 4. Human escalation
    if intent == "escalate":
        try:
            ticket = create_ticket(
                name,
                "human_escalation",
                "high",
                message,
            )

            result = (
                "I've recorded your request for a human support "
                f"representative as ticket {ticket['ticket_id']}. "
                "Status: open. This demo does not send a real "
                "notification, so a representative has not yet "
                "been directly contacted."
            )
        except Exception:
            result = (
                "I couldn't create an escalation ticket right now. "
                "Please try again or contact support directly."
            )

        return {
            "intent": intent,
            "tool_result": result,
        }

    # 5. New support issue
    if intent == "ticket":
        low = message.lower()

        priority = (
            "high"
            if any(
                phrase in low
                for phrase in (
                    "charged twice",
                    "double charge",
                    "duplicate charge",
                    "fraud",
                    "unsafe",
                    "urgent",
                    "damaged",
                )
            )
            else "normal"
        )

        category = (
            "billing"
            if any(
                phrase in low
                for phrase in (
                    "payment",
                    "charged",
                    "billing",
                    "refund",
                    "duplicate charge",
                    "double charge",
                )
            )
            else "product_support"
        )

        try:
            ticket = create_ticket(
                name,
                category,
                priority,
                message,
            )

            result = (
                "I'm sorry you're experiencing this. "
                "I've recorded the issue.\n\n"
                f"Created support ticket {ticket['ticket_id']} "
                f"(priority: {priority}, status: open).\n\n"
                "Please keep the ticket ID for reference."
            )
        except Exception:
            result = (
                "I'm sorry you're experiencing this. "
                "I couldn't create a support ticket right now. "
                "Please try again."
            )

        return {
            "intent": intent,
            "tool_result": result,
        }

    # 6. FAQ knowledge retrieval
    try:
        context = search_faqs(message)
        result = str(context) if context else ""
    except Exception:
        result = ""

    return {
        "intent": "faq",
        "tool_result": result,
    }


# --------------------------------------------------
# Generate final response
# --------------------------------------------------
def _format_answer(
    message: str,
    intent: str,
    result: str,
) -> str:

    # Greetings and tool results need no LLM.
    if intent in ("greeting", "order", "ticket", "escalate"):
        return result

    if intent == "ticket_lookup":
        return result

    # Missing knowledge
    if not result.strip():
        return (
            "I'm sorry, but I couldn't find enough information "
            "in the current knowledge base to answer that question. "
            "Would you like me to create a support ticket so our "
            "team can help?"
        )

    # No API key: return retrieved knowledge directly.
    if not GROQ_API_KEY:
        return (
            "Here is the most relevant information I found in "
            "the demo knowledge base:\n\n"
            f"{result}\n\n"
            "If this doesn't resolve your question, I can help "
            "you create a support ticket."
        )

    # Grounded LLM response
    try:
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model=MODEL_NAME,
            temperature=0.2,
            api_key=GROQ_API_KEY,
        )

        response = llm.invoke(
            [
                (
                    "system",
                    """
                    You are a professional customer support assistant.

                    Rules:
                    - Answer using only the supplied company context.
                    - Never invent return policies, refund terms, or order details.
                    - If the context does not answer the question, say so.
                    - Offer to create a support ticket when appropriate.
                    - Never claim to have performed an action unless a tool result confirms it.
                    - Be polite, concise, and clear.
                    """,
                ),
                (
                    "human",
                    f"Customer message:\n{message}\n\n"
                    f"Company knowledge context:\n{result}",
                ),
            ]
        )

        return str(response.content)

    except Exception:
        return (
            "I found relevant information, but the AI model is "
            "temporarily unavailable.\n\n"
            f"{result}\n\n"
            "Please try again later or ask me to create a support ticket."
        )


# --------------------------------------------------
# Build LangGraph
# --------------------------------------------------
def build_graph():
    graph = StateGraph(SupportState)

    graph.add_node("run_tool", _run_tool)

    graph.add_node(
        "respond",
        lambda state: {
            "answer": _format_answer(
                state["message"],
                state.get("intent", "faq"),
                state.get("tool_result", ""),
            )
        },
    )

    graph.set_entry_point("run_tool")
    graph.add_edge("run_tool", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


# --------------------------------------------------
# Public entry point
# --------------------------------------------------
_support_graph = None


def answer_customer(
    message: str,
    customer_name: str = "Demo Customer",
) -> dict:
    global _support_graph

    if _support_graph is None:
        _support_graph = build_graph()

    result = _support_graph.invoke(
        {
            "message": message,
            "customer_name": customer_name,
        }
    )

    return {
        "answer": result["answer"],
        "intent": result.get("intent", "faq"),
    }
