
import sys
from pathlib import Path

import streamlit as st

# --------------------------------------------------
# Project configuration
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agent import answer_customer
from app.db import init_db, list_tickets, log_chat


# --------------------------------------------------
# Streamlit page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="AI Customer Support",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# --------------------------------------------------
# Custom styling
# --------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* Chat history container */
    .st-key-chat_history {
        border: 1px solid rgba(128, 128, 128, 0.30);
        border-radius: 14px;
        padding: 12px;
        background-color: transparent;
    }

    /* Keep chat content readable */
    .st-key-chat_history [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
    }

    /* Sidebar spacing */
    [data-testid="stSidebar"] {
        padding-top: 1rem;
    }

    /* Chat input styling */
    [data-testid="stChatInput"] {
        padding-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm your AI support assistant. "
                "Ask about policies, check a demo order, "
                "or tell me about an issue."
            ),
        }
    ]

if "suggested_prompt" not in st.session_state:
    st.session_state.suggested_prompt = None

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("💬 AI Customer Support Agent")

st.caption(
    "Client showcase demo • FAQ assistant • Order lookup "
    "• Support tickets • Human escalation"
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("⚙️ Demo controls")

    customer_name = st.text_input(
        "Customer name",
        value="Alex",
    )

    st.markdown("**Try these prompts**")

    example_prompts = [
        "What is your return policy?",
        "Where is order ORD-1001?",
        "My payment was charged twice.",
        "I want to speak to a human.",
    ]

    for example in example_prompts:
        if st.button(
            example,
            key=f"prompt_{example}",
            use_container_width=True,
        ):
            st.session_state.suggested_prompt = example
            st.rerun()

    st.divider()

    st.subheader("🎫 Recent support tickets")

    tickets = list_tickets(10)

    if tickets:
        for ticket in tickets:
            with st.container(border=True):
                st.markdown(f"**{ticket['ticket_id']}**")

                st.caption(
                    f"Priority: {ticket['priority'].upper()} "
                    f"· Status: {ticket['status']}"
                )

                st.write(ticket["issue"][:100])

    else:
        st.caption("No tickets yet.")

# --------------------------------------------------
# Chat history
# IMPORTANT: Only this container scrolls.
# --------------------------------------------------
st.subheader("Conversation")

with st.container(
    height=520,
    border=True,
    key="chat_history",
):
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --------------------------------------------------
# Chat input
# Keep outside the scrollable chat container.
# --------------------------------------------------
suggested = st.session_state.suggested_prompt

prompt = st.chat_input(
    "How can I help you today?",
)

# Handle sidebar example prompts.
if suggested:
    prompt = suggested
    st.session_state.suggested_prompt = None

# --------------------------------------------------
# Process customer message
# --------------------------------------------------
if prompt:
    # Store the user's message.
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:
        with st.spinner("Checking your request..."):
            result = answer_customer(
                prompt,
                customer_name.strip() or "Customer",
            )

            answer = result.get(
                "answer",
                "I couldn't generate a response. Please try again.",
            )

    except Exception:
        answer = (
            "I'm sorry, but something went wrong while "
            "processing your request. Please try again."
        )

    # Store the assistant response.
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    # Save conversation to the database.
    try:
        log_chat(prompt, answer)
    except Exception:
        st.warning(
            "The response was generated, but the chat "
            "could not be saved to the database."
        )

    # Rerender the UI with the updated conversation.
    st.rerun()
