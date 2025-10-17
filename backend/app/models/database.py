"""
Database models for the Customer Support Bot
Tables: User, Session, Message, Escalation, FAQDocument
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """
    User model to store customer information
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), index=True, nullable=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """
    Session model to store conversation sessions
    Tracks active conversations and their metadata
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    topic = Column(String(255), nullable=True)
    status = Column(String(50), default="active")  # active, closed, escalated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    conversation_summary = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    escalation = relationship("Escalation", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Message(Base):
    """
    Message model to store conversation messages
    Stores both user and bot messages with metadata
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True, nullable=False)
    sender = Column(String(50), nullable=False)  # "user" or "bot"
    content = Column(Text, nullable=False)
    response_type = Column(String(50), nullable=True)  # "faq", "escalated", "clarification"
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence in the response
    relevant_faq_ids = Column(JSON, nullable=True)  # List of FAQ document IDs used
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("Session", back_populates="messages")


class Escalation(Base):
    """
    Escalation model to track support tickets
    Created when the bot cannot confidently answer queries
    """
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    escalation_id = Column(String(100), unique=True, index=True, nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    reason = Column(Text, nullable=False)
    initial_query = Column(Text, nullable=False)
    conversation_context = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, resolved
    assigned_to = Column(String(255), nullable=True)
    priority = Column(String(50), default="normal")  # low, normal, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="escalations")
    session = relationship("Session", back_populates="escalation")


class FAQDocument(Base):
    """
    FAQ Document model to store FAQ knowledge base
    Supports semantic search through embeddings
    """
    __tablename__ = "faq_documents"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(255), nullable=True)
    keywords = Column(JSON, nullable=True)  # List of keywords for quick matching
    embedding = Column(JSON, nullable=True)  # Vector embedding for semantic search
    source = Column(String(255), nullable=True)  # PDF source filename
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class ConversationMetrics(Base):
    """
    Conversation metrics for analytics and monitoring
    """
    __tablename__ = "conversation_metrics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    total_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)
    bot_messages = Column(Integer, default=0)
    average_confidence_score = Column(Float, nullable=True)
    escalation_count = Column(Integer, default=0)
    resolution_time_minutes = Column(Integer, nullable=True)
    was_escalated = Column(Boolean, default=False)
    was_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
