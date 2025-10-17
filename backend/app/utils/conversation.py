"""
Conversation Logic
Handles contextual memory, escalation detection, summarization, and next-action suggestions
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from sqlalchemy.orm import Session
from app.models.database import (
    Session as DBSession,
    Message,
    Escalation,
    ConversationMetrics,
)
from app.utils.embeddings import get_faq_context
from app.utils.llm_integration import llm_manager

logger = logging.getLogger(__name__)

# Threshold for escalation (confidence below this triggers escalation)
ESCALATION_THRESHOLD = 0.5
# Keywords that might indicate escalation need
ESCALATION_KEYWORDS = [
    "urgent", "emergency", "critical", "problem", "bug", "error",
    "broken", "not working", "complaint", "refund", "cancel", "angry",
]


def build_conversation_context(
    session: DBSession,
    db: Session,
    max_messages: int = 10,
) -> str:
    """
    Build conversation context from message history
    
    Args:
        session: DB Session object
        db: Database session
        max_messages: Maximum number of messages to include
        
    Returns:
        Formatted conversation context
    """
    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.desc())
        .limit(max_messages)
        .all()
    )

    messages.reverse()  # Chronological order

    context_parts = []
    for msg in messages:
        sender = "Customer" if msg.sender == "user" else "Support"
        context_parts.append(f"{sender}: {msg.content}")

    return "\n".join(context_parts)


async def detect_escalation_need(
    query: str,
    faq_context: str,
    context_confidence: float,
) -> Tuple[bool, str]:
    """
    Detect if query should be escalated based on confidence and keywords
    
    Args:
        query: User query
        faq_context: Retrieved FAQ context
        context_confidence: Confidence score for the FAQ context
        
    Returns:
        Tuple of (should_escalate, reason)
    """
    # Check confidence threshold
    if context_confidence < ESCALATION_THRESHOLD:
        return True, f"Low confidence in FAQ match (score: {context_confidence:.2f})"

    # Check for escalation keywords
    query_lower = query.lower()
    for keyword in ESCALATION_KEYWORDS:
        if keyword in query_lower:
            return True, f"Query contains sensitive keyword: '{keyword}'"

    # If no FAQ context found
    if not faq_context.strip():
        return True, "No relevant FAQ found for this query"

    return False, ""


async def generate_bot_response(
    query: str,
    faq_context: str,
    conversation_history: str,
    should_escalate: bool = False,
) -> str:
    """
    Generate bot response using LLM with FAQ context
    
    Args:
        query: User query
        faq_context: Retrieved FAQ context
        conversation_history: Previous conversation context
        should_escalate: Whether the query should be escalated
        
    Returns:
        Bot response text
    """
    if should_escalate:
        return (
            "I appreciate your question. This seems like something that requires "
            "specialized attention. I'll forward this to a support specialist for "
            "better assistance. They'll get back to you shortly with a detailed response."
        )

    # Build system prompt with FAQ context
    system_prompt = """You are a helpful customer support AI assistant. Your goal is to provide accurate, 
concise, and friendly responses to customer inquiries based on the FAQ knowledge base provided.

Guidelines:
1. Always be polite and professional
2. Use the FAQ context to answer questions accurately
3. If the FAQ context doesn't fully address the query, acknowledge it and provide helpful guidance
4. Keep responses concise (2-3 sentences max)
5. If you can't answer with certainty, say "I'll forward this to a support specialist for better assistance"

FAQ Knowledge Base:
{faq_context}

Conversation History:
{conversation_history}
"""

    user_prompt = f"Customer Question: {query}\n\nPlease provide a helpful response based on the knowledge base above."

    try:
        response = await llm_manager.generate_response(
            prompt=user_prompt,
            system_message=system_prompt.format(
                faq_context=faq_context or "No relevant FAQ found",
                conversation_history=conversation_history or "This is the start of the conversation"
            ),
            temperature=0.7,
            max_tokens=300,
        )
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I'm experiencing technical difficulties. Please try again or contact our support team."


async def generate_conversation_summary(
    session: DBSession,
    db: Session,
) -> str:
    """
    Generate a summary of the conversation
    
    Args:
        session: DB Session object
        db: Database session
        
    Returns:
        Conversation summary
    """
    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    if not messages:
        return "No messages in this conversation."

    conversation_text = "\n".join(
        [f"{msg.sender}: {msg.content}" for msg in messages]
    )

    prompt = f"""Summarize the following customer support conversation in 2-3 sentences, 
highlighting the main issue and whether it was resolved:

{conversation_text}

Summary:"""

    try:
        summary = await llm_manager.generate_response(
            prompt=prompt,
            temperature=0.5,
            max_tokens=150,
        )
        return summary.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Unable to generate summary"


async def suggest_next_actions(
    session: DBSession,
    db: Session,
) -> Dict[str, Any]:
    """
    Suggest next actions based on conversation
    
    Args:
        session: DB Session object
        db: Database session
        
    Returns:
        Dictionary with suggested actions
    """
    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    if not messages:
        return {"actions": [], "confidence": 0.0}

    conversation_text = "\n".join(
        [f"{msg.sender}: {msg.content}" for msg in messages[-10:]]  # Last 10 messages
    )

    prompt = f"""Based on this customer support conversation, suggest 2-3 specific next actions 
the support team should take. Consider: was the issue resolved? Does it need escalation? 
Are there any follow-ups needed?

Conversation:
{conversation_text}

Provide your response as a JSON object with "actions" as a list of strings and "recommend_escalation" as boolean."""

    try:
        response = await llm_manager.generate_response(
            prompt=prompt,
            temperature=0.5,
            max_tokens=200,
        )

        # Try to parse JSON from response
        import json
        # Extract JSON from response
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)
            return {
                "actions": parsed.get("actions", []),
                "confidence": 0.8,
                "recommend_escalation": parsed.get("recommend_escalation", False),
            }

        return {"actions": ["Continue monitoring the conversation"], "confidence": 0.5}

    except Exception as e:
        logger.error(f"Error suggesting next actions: {e}")
        return {"actions": [], "confidence": 0.0}


def create_escalation(
    session: DBSession,
    user_id: int,
    reason: str,
    initial_query: str,
    conversation_context: Dict[str, Any],
    db: Session,
    priority: str = "normal",
) -> Escalation:
    """
    Create an escalation ticket
    
    Args:
        session: DB Session object
        user_id: User ID
        reason: Escalation reason
        initial_query: Initial customer query
        conversation_context: Conversation context data
        db: Database session
        priority: Priority level
        
    Returns:
        Created Escalation object
    """
    import uuid

    escalation = Escalation(
        escalation_id=f"ESC-{uuid.uuid4().hex[:8].upper()}",
        session_id=session.id,
        user_id=user_id,
        reason=reason,
        initial_query=initial_query,
        conversation_context=conversation_context,
        status="pending",
        priority=priority,
    )

    # Update session status
    session.status = "escalated"

    db.add(escalation)
    db.commit()

    logger.info(f"Created escalation: {escalation.escalation_id}")
    return escalation


def get_conversation_metrics(
    session: DBSession,
    db: Session,
) -> Dict[str, Any]:
    """
    Calculate metrics for a conversation
    
    Args:
        session: DB Session object
        db: Database session
        
    Returns:
        Dictionary with conversation metrics
    """
    messages = db.query(Message).filter(Message.session_id == session.id).all()

    user_messages = [m for m in messages if m.sender == "user"]
    bot_messages = [m for m in messages if m.sender == "bot"]

    confidence_scores = [
        m.confidence_score for m in bot_messages if m.confidence_score is not None
    ]

    duration = None
    if messages:
        start_time = messages[0].created_at
        end_time = messages[-1].created_at
        duration = int((end_time - start_time).total_seconds() / 60)

    return {
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "bot_messages": len(bot_messages),
        "average_confidence": (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        ),
        "duration_minutes": duration,
        "is_escalated": session.status == "escalated",
    }


def update_conversation_metrics(
    session: DBSession,
    db: Session,
) -> ConversationMetrics:
    """
    Update conversation metrics in database
    
    Args:
        session: DB Session object
        db: Database session
        
    Returns:
        Updated ConversationMetrics object
    """
    metrics = get_conversation_metrics(session, db)

    metrics_obj = (
        db.query(ConversationMetrics)
        .filter(ConversationMetrics.session_id == session.id)
        .first()
    )

    if not metrics_obj:
        metrics_obj = ConversationMetrics(session_id=session.id)

    metrics_obj.total_messages = metrics["total_messages"]
    metrics_obj.user_messages = metrics["user_messages"]
    metrics_obj.bot_messages = metrics["bot_messages"]
    metrics_obj.average_confidence_score = metrics["average_confidence"]
    metrics_obj.resolution_time_minutes = metrics["duration_minutes"]
    metrics_obj.was_escalated = metrics["is_escalated"]

    db.add(metrics_obj)
    db.commit()

    return metrics_obj
