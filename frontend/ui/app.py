"""
Streamlit Frontend for AI Customer Support Bot
Interactive chat interface with session management and conversation history
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="AI Customer Support Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4CAF50;
    }
    .escalated-message {
        background-color: #fff3e0;
        border-left: 4px solid #FF9800;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: bold;
        margin-top: 0.5rem;
        margin-right: 0.5rem;
    }
    .confidence-high {
        background-color: #c8e6c9;
        color: #1b5e20;
    }
    .confidence-medium {
        background-color: #ffe0b2;
        color: #e65100;
    }
    .confidence-low {
        background-color: #ffcdd2;
        color: #b71c1c;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = f"customer-{uuid.uuid4().hex[:8]}"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_summary" not in st.session_state:
        st.session_state.conversation_summary = None
    if "is_escalated" not in st.session_state:
        st.session_state.is_escalated = False


def get_confidence_color(confidence: float) -> str:
    """Get color class based on confidence score"""
    if confidence >= 0.7:
        return "confidence-high"
    elif confidence >= 0.4:
        return "confidence-medium"
    else:
        return "confidence-low"


def send_message(user_message: str) -> Optional[Dict]:
    """Send message to the bot"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "session_id": st.session_state.session_id,
                "customer_id": st.session_state.customer_id,
                "message": user_message,
                "conversation_history": [
                    {"sender": msg["sender"], "content": msg["content"]}
                    for msg in st.session_state.messages
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with server: {e}")
        return None


def display_message(sender: str, content: str, metadata: Dict = None):
    """Display a message in the chat interface"""
    if sender == "user":
        css_class = "user-message"
        icon = "👤"
        label = "You"
    else:
        if metadata and metadata.get("requires_escalation"):
            css_class = "escalated-message"
            icon = "⚠️"
            label = "Support Team (Escalated)"
        else:
            css_class = "bot-message"
            icon = "🤖"
            label = "Support Bot"

    # Display icon and label on same line
    st.markdown(f"### {icon} {label}")

    st.markdown(f'<div class="chat-message {css_class}">{content}</div>', unsafe_allow_html=True)

    # Display metadata if available
    # if metadata:
    #     col1, col2, col3, col4 = st.columns(4)

    #     if metadata.get("confidence_score") is not None:
    #         with col1:
    #             confidence = metadata["confidence_score"]
    #             color_class = get_confidence_color(confidence)
    #             st.markdown(
    #                 f'<span class="confidence-badge {color_class}">Confidence: {confidence:.1%}</span>',
    #                 unsafe_allow_html=True,
    #             )

    #     if metadata.get("response_type"):
    #         with col2:
    #             response_type = metadata["response_type"]
    #             if response_type == "faq":
    #                 st.success("📚 From FAQ")
    #             elif response_type == "escalated":
    #                 st.warning("⚠️ Escalated")

    #     if metadata.get("requires_escalation"):
    #         with col3:
    #             st.error("🚨 Escalation Initiated")

    #     if metadata.get("relevant_faqs"):
    #         with col4:
    #             with st.expander(f"📖 Related FAQs ({len(metadata['relevant_faqs'])})"):
    #                 for faq in metadata["relevant_faqs"]:
    #                     st.markdown(f"**Q:** {faq['question']}")
    #                     st.markdown(f"**A:** {faq['answer']}")


def main():
    """Main Streamlit app"""
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.title("🤖 Support Bot")

        # New Conversation Button
        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.is_escalated = False
            st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
            st.session_state.customer_id = f"customer-{uuid.uuid4().hex[:8]}"
            st.rerun()

        st.divider()

        # FAQ Management Section
        st.subheader("📚 FAQ Management")
        
        # Upload FAQ PDF
        uploaded_file = st.file_uploader(
            "Upload FAQs PDF",
            type="pdf",
            help="Upload a PDF with Q&A format. Format: Q: Question?\nA: Answer",
        )
        
        if uploaded_file is not None:
            if st.button("📤 Upload & Process FAQ", use_container_width=True):
                with st.spinner("Processing PDF..."):
                    try:
                        # Upload to backend
                        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                        response = requests.post(
                            f"{API_BASE_URL}/faqs/upload",
                            files=files,
                            timeout=60,
                        )
                        response.raise_for_status()
                        result = response.json()
                        
                        if result.get("success"):
                            st.success(
                                f"✅ {result['message']}\n"
                                f"Total FAQs in system: {result['total_faqs_in_system']}"
                            )
                        else:
                            st.error(f"Error: {result.get('message', 'Unknown error')}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Upload failed: {e}")
        
        # Show FAQ count and clear button
        try:
            response = requests.get(f"{API_BASE_URL}/faqs", timeout=10)
            if response.status_code == 200:
                faq_data = response.json()
                total_faqs = faq_data.get("total_faqs", 0)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📖 Total FAQs", total_faqs)
                with col2:
                    if st.button("🗑️ Clear All FAQs", use_container_width=True):
                        with st.spinner("Clearing FAQs..."):
                            try:
                                response = requests.delete(
                                    f"{API_BASE_URL}/faqs/clear/all",
                                    timeout=30,
                                )
                                response.raise_for_status()
                                result = response.json()
                                
                                if result.get("success"):
                                    st.success(f"✅ {result['message']}")
                                    st.info("Upload new FAQ PDF to continue")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {result.get('message', 'Unknown error')}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Clear failed: {e}")
        except:
            st.metric("📖 Total FAQs", "N/A")

        st.divider()

        # Session info
        st.subheader("Session Information")
        st.text_input("Session ID", value=st.session_state.session_id, disabled=True)
        st.text_input("Customer ID", value=st.session_state.customer_id, disabled=True)

        st.divider()

        # Status
        st.subheader("Status")
        if st.session_state.is_escalated:
            st.warning("🚨 Escalated to human specialist")
        else:
            st.success("✅ Connected to AI for customer support")

    # Main chat area
    st.title("💬 AI Customer Support Chatbot")

    # Display chat history
    st.subheader("Conversation")
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            display_message(msg["sender"], msg["content"], msg.get("metadata"))

    st.divider()

    # Input area
    col1, col2 = st.columns([9, 1])

    with col1:
        user_input = st.text_input(
            "Type your question here...",
            placeholder="How can I help you today?",
            label_visibility="collapsed",
            key="user_input",
        )

    with col2:
        send_button = st.button("Send", key="send_button", use_container_width=True)

    # Process user input
    if send_button and user_input.strip():
        # Add user message to state
        st.session_state.messages.append(
            {"sender": "user", "content": user_input, "metadata": {}}
        )

        # Send to bot
        with st.spinner("🤖 Processing..."):
            response = send_message(user_input)

        if response:
            # Check for escalation
            if response.get("requires_escalation"):
                st.session_state.is_escalated = True

            # Add bot response to state
            st.session_state.messages.append(
                {
                    "sender": "bot",
                    "content": response["bot_response"],
                    "metadata": {
                        "confidence_score": response.get("confidence_score"),
                        "response_type": response.get("response_type"),
                        "requires_escalation": response.get("requires_escalation"),
                        "relevant_faqs": response.get("relevant_faqs"),
                    },
                }
            )

            # Show escalation notification
            if response.get("requires_escalation"):
                st.warning(
                    "🚨 This conversation has been escalated to a human specialist. "
                    "You'll be connected shortly."
                )

        # Clear input by deleting key from session state
        del st.session_state.user_input
        st.rerun()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.is_escalated = False
            st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
            st.rerun()

    with col2:
        st.markdown("Powered by OpenRouter GPT-OSS 20B | FastAPI | Streamlit")

    with col3:
        st.markdown("Version 1.0.0")


if __name__ == "__main__":
    main()
