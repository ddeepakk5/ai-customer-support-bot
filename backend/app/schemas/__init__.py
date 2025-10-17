"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    name: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    sender: str = Field(..., pattern="^(user|bot)$")


class MessageResponse(MessageBase):
    id: int
    sender: str
    response_type: Optional[str] = None
    confidence_score: Optional[float] = None
    relevant_faq_ids: Optional[List[int]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    session_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    session_id: str
    user_message: str
    bot_response: str
    confidence_score: float
    response_type: str  # "faq", "escalated", "clarification"
    requires_escalation: bool
    relevant_faqs: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime


class FAQDocumentBase(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    keywords: Optional[List[str]] = None


class FAQDocumentCreate(FAQDocumentBase):
    pass


class FAQDocumentResponse(FAQDocumentBase):
    id: int
    source: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    topic: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionResponse(SessionBase):
    session_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    conversation_summary: Optional[str] = None

    class Config:
        from_attributes = True


class EscalationBase(BaseModel):
    reason: str
    initial_query: str
    priority: Optional[str] = "normal"


class EscalationCreate(EscalationBase):
    pass


class EscalationResponse(EscalationBase):
    escalation_id: str
    session_id: int
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationSummaryRequest(BaseModel):
    session_id: str


class ConversationSummaryResponse(BaseModel):
    session_id: str
    summary: str
    key_topics: List[str]
    resolution_status: str
    suggested_next_actions: List[str]
    total_messages: int
    duration_minutes: Optional[int] = None


class NextActionSuggestionResponse(BaseModel):
    session_id: str
    suggested_actions: List[Dict[str, str]]
    confidence: float
    recommended_escalation: bool
    escalation_reason: Optional[str] = None
