"""
FastAPI routes for customer support chatbot
- FAQ-first approach: only answers from FAQ database
- Uses AI to determine if off-topic queries are related to FAQs
- Raises tickets for out-of-scope questions
- Guides users to ask product/service-related questions
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models import get_db
from app.schemas import ChatRequest, ChatResponse, SessionResponse
from app.models.database import User, Session as DBSession, Message, Escalation, FAQDocument
from app.utils.llm_integration import llm_manager
from datetime import datetime
import uuid
import logging
import os
import tempfile

logger = logging.getLogger(__name__)
router = APIRouter()

# FAQ dataset loaded from database
FAQ_DATASET = {}


def load_faq_dataset(db: Session) -> dict:
    """Load all active FAQs from database into memory"""
    global FAQ_DATASET
    faqs = db.query(FAQDocument).filter(FAQDocument.is_active == True).all()
    
    FAQ_DATASET.clear()
    for faq in faqs:
        # Use question as key, answer as value
        key = faq.question.lower()[:100]
        FAQ_DATASET[key] = {
            "answer": faq.answer,
            "category": faq.category,
            "id": faq.id,
            "keywords": faq.keywords or [],
        }
    
    logger.info(f"Loaded {len(FAQ_DATASET)} FAQs from database")
    return FAQ_DATASET


def search_faq_dataset(query: str, faq_dataset: dict) -> tuple:
    """
    Search FAQ dataset using keyword matching
    Returns: (faq_id, answer, confidence_score, found_match)
    
    Matching logic:
    - Direct keyword match in question (0.9 confidence)
    - Word match in question (0.7 confidence)
    - Keyword match in FAQ keywords (0.6 confidence)
    """
    query_lower = query.lower()
    best_match = None
    best_confidence = 0.0
    
    for faq_question, faq_data in faq_dataset.items():
        # Direct question match
        if query_lower in faq_question or faq_question in query_lower:
            confidence = 0.9
            if confidence > best_confidence:
                best_match = faq_data
                best_confidence = confidence
            continue
        
        # Word-level matching in question
        question_words = faq_question.split()
        query_words = query_lower.split()
        matched_words = sum(1 for w in question_words if w in query_words)
        
        if matched_words > 0:
            confidence = 0.6 + (matched_words / len(question_words)) * 0.3
            if confidence > best_confidence:
                best_match = faq_data
                best_confidence = confidence
        
        # Keyword matching
        faq_keywords = faq_data.get("keywords", [])
        if faq_keywords:
            matched_keywords = sum(1 for kw in faq_keywords if kw.lower() in query_lower)
            if matched_keywords > 0:
                confidence = 0.5 + (matched_keywords / len(faq_keywords)) * 0.2
                if confidence > best_confidence:
                    best_match = faq_data
                    best_confidence = confidence
    
    if best_match and best_confidence >= 0.5:
        return best_match["id"], best_match["answer"], best_confidence, True
    
    return None, "", 0.0, False


async def check_relevance_with_ai(query: str, conversation_context: str) -> tuple:
    """
    Use AI to determine if query is related to product/service FAQs
    Returns: (is_related_to_faqs, category, confidence)
    """
    relevance_prompt = f"""Analyze if this customer question is related to product/service support and FAQs.

Customer Question: {query}

Previous Conversation:
{conversation_context if conversation_context else "No previous conversation"}

Respond in this exact JSON format:
{{"is_related": true/false, "category": "category_name", "confidence": 0.0-1.0, "reason": "brief reason"}}

Only respond with the JSON, no other text.

Guidelines:
- is_related: true if question is about product features, account, billing, passwords, features, technical support
- is_related: false if question is about unrelated topics (politics, personal advice, jokes, etc.)
- category: probable FAQ category if related, empty string if not
- confidence: how confident you are (0.5-1.0)
"""
    
    try:
        response_text = await llm_manager.generate_response(
            prompt=relevance_prompt,
            system_message="You are an AI that classifies customer support questions. Respond ONLY with valid JSON.",
            temperature=0.3,
            max_tokens=150,
        )
        
        # Parse JSON response
        import json
        response_text = response_text.strip()
        
        # Find JSON in response
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                return (
                    result.get("is_related", False),
                    result.get("category", ""),
                    result.get("confidence", 0.0),
                )
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from AI response: {response_text}")
        
        return False, "", 0.0
        
    except Exception as e:
        logger.error(f"Error checking relevance with AI: {e}")
        return False, "", 0.0
def build_conversation_context(session: DBSession, db: Session, max_messages: int = 5) -> str:
    """Build conversation history for context"""
    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.desc())
        .limit(max_messages)
        .all()
    )
    
    messages.reverse()
    context_parts = []
    for msg in messages:
        sender = "Customer" if msg.sender == "user" else "Support"
        context_parts.append(f"{sender}: {msg.content}")
    
    return "\n".join(context_parts) if context_parts else ""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint with FAQ-first approach
    
    Flow:
    1. Search FAQ database for direct match → Answer from FAQ
    2. No match → Use AI to check if question is related to FAQs
    3. Related → Create ticket (agent will research and answer)
    4. Not related → Ask to ask product/service questions only
    """
    try:
        # Reload FAQ dataset from database
        load_faq_dataset(db)
        
        # Get or create user
        user = db.query(User).filter(User.customer_id == request.customer_id).first()
        if not user:
            user = User(customer_id=request.customer_id)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Get or create session
        session = db.query(DBSession).filter(DBSession.session_id == request.session_id).first()
        if not session:
            session = DBSession(
                session_id=request.session_id,
                user_id=user.id,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        # Store user message
        user_msg = Message(
            session_id=session.id,
            sender="user",
            content=request.message,
        )
        db.add(user_msg)
        db.commit()

        # Get conversation history for context
        conversation_context = build_conversation_context(session, db)

        # STEP 1: Search FAQ dataset for direct match
        faq_id, faq_answer, faq_confidence, faq_found = search_faq_dataset(
            request.message, FAQ_DATASET
        )

        if faq_found and faq_confidence >= 0.5:
            # Direct FAQ match found - answer directly
            bot_response = faq_answer
            response_type = "faq"
            should_escalate = False
            confidence_score = faq_confidence

            logger.info(f"FAQ match found with confidence {faq_confidence}")

        else:
            # STEP 2: No direct FAQ match - check if related using AI
            is_related, category, relevance_confidence = await check_relevance_with_ai(
                request.message, conversation_context
            )

            if is_related and relevance_confidence >= 0.6:
                # Question is related to product/service but not in FAQ
                # Generate response using GPT-OSS model
                try:
                    gpt_prompt = f"""You are a helpful customer support assistant. Answer this customer question accurately and professionally based on your knowledge about common product/service support topics.

Customer Question: {request.message}

Previous Context: {conversation_context if conversation_context else 'No previous conversation'}

Provide a helpful, clear, and concise answer. If you're not completely sure about something, acknowledge it and suggest they contact the support team for clarification."""

                    bot_response = await llm_manager.generate_response(
                        prompt=gpt_prompt,
                        system_message="You are a professional customer support representative. Provide helpful and accurate responses to customer inquiries.",
                        temperature=0.7,
                        max_tokens=500,
                    )
                    
                    response_type = "ai_generated"
                    should_escalate = False
                    confidence_score = 0.65
                    
                    logger.info(f"Generated response using GPT-OSS model for related question")
                    
                except Exception as e:
                    logger.error(f"Error generating response with GPT-OSS: {e}")
                    # Fallback to escalation if AI generation fails
                    escalation = Escalation(
                        escalation_id=f"ticket-{uuid.uuid4().hex[:8]}",
                        session_id=session.id,
                        user_id=user.id,
                        reason=f"Customer question related to {category} - AI generation failed",
                        initial_query=request.message,
                        status="pending",
                        priority="normal",
                    )
                    db.add(escalation)
                    session.status = "escalated"
                    db.commit()
                    
                    bot_response = (
                        f"Thank you for your question! We're connecting you to our support team now. "
                        f"A specialist will be with you shortly to assist with your inquiry.\n\n"
                        f"Ticket ID: {escalation.escalation_id}\n\n"
                        f"Please stay in this chat and someone from our team will respond shortly."
                    )
                    response_type = "escalated"
                    should_escalate = True
                    confidence_score = 0.0

            else:
                # Question is NOT related to product/service - escalate
                escalation = Escalation(
                    escalation_id=f"ticket-{uuid.uuid4().hex[:8]}",
                    session_id=session.id,
                    user_id=user.id,
                    reason="Off-topic question - not related to products/services",
                    initial_query=request.message,
                    status="pending",
                    priority="low",
                )
                db.add(escalation)
                session.status = "escalated"
                db.commit()
                
                bot_response = (
                    "I'm here to help with questions about our products and services. "
                    "Your question doesn't seem to be related to our offerings.\n\n"
                    "If you have any product or service-related questions, I'd be happy to help!\n\n"
                    "For other inquiries, you can contact our support team at support@example.com"
                )
                response_type = "out_of_scope"
                should_escalate = True
                confidence_score = 0.0

                logger.info(f"Out-of-scope question escalated: {request.message}")

        # Store bot response
        bot_msg = Message(
            session_id=session.id,
            sender="bot",
            content=bot_response,
            response_type=response_type,
            confidence_score=confidence_score,
            relevant_faq_ids=[faq_id] if faq_id else None,
        )
        db.add(bot_msg)
        db.commit()

        return ChatResponse(
            session_id=request.session_id,
            user_message=request.message,
            bot_response=bot_response,
            confidence_score=confidence_score,
            response_type=response_type,
            requires_escalation=should_escalate,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=SessionResponse)
async def create_session(customer_id: str, db: Session = Depends(get_db)):
    """Create a new chat session"""
    try:
        user = db.query(User).filter(User.customer_id == customer_id).first()
        if not user:
            user = User(customer_id=customer_id)
            db.add(user)
            db.commit()
            db.refresh(user)

        session = DBSession(
            session_id=f"session-{uuid.uuid4().hex[:8]}",
            user_id=user.id,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return SessionResponse(
            session_id=session.session_id,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faqs/upload")
async def upload_faq_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a PDF containing FAQs
    Clears existing FAQs and stores new ones from the PDF
    
    Expected PDF format:
    Q: Question text?
    A: Answer text
    
    Q: Another question?
    A: Another answer
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    temp_path = None
    try:
        # Clear existing FAQs first
        deleted_count = db.query(FAQDocument).filter(
            FAQDocument.is_active == True
        ).update({"is_active": False})
        db.commit()
        logger.info(f"Cleared {deleted_count} existing FAQs before uploading new ones")
        
        # Save uploaded file to temporary location
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, 'wb') as f:
            contents = await file.read()
            f.write(contents)
        
        logger.info(f"Processing PDF: {file.filename}")
        
        # Import pdf processor
        from app.utils.pdf_processor import extract_text_from_pdf, parse_faq_content
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(temp_path)
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Parse FAQ content
        faqs = parse_faq_content(text_content)
        if not faqs:
            raise HTTPException(
                status_code=400,
                detail="No FAQ format detected. Please format as:\nQ: Question?\nA: Answer"
            )
        
        # Store FAQs in database
        stored_count = 0
        for question, answer, category in faqs:
            if question and answer:
                try:
                    faq_doc = FAQDocument(
                        question=question[:1000],
                        answer=answer[:5000],
                        category=category,
                        keywords=[],
                        source=file.filename,
                        is_active=True,
                    )
                    db.add(faq_doc)
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing FAQ: {e}")
                    continue
        
        db.commit()
        
        # Reload FAQ dataset
        load_faq_dataset(db)
        
        logger.info(f"Successfully stored {stored_count} FAQs from {file.filename}")
        
        return {
            "success": True,
            "message": f"✅ Successfully extracted and stored {stored_count} FAQs",
            "faqs_added": stored_count,
            "filename": file.filename,
            "total_faqs_in_system": len(FAQ_DATASET),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")


@router.get("/faqs")
async def get_faqs(db: Session = Depends(get_db)):
    """Get all FAQs in the system"""
    load_faq_dataset(db)
    
    all_faqs = db.query(FAQDocument).filter(FAQDocument.is_active == True).all()
    
    return {
        "total_faqs": len(all_faqs),
        "faqs": [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "category": faq.category,
                "source": faq.source,
            }
            for faq in all_faqs
        ],
    }


@router.delete("/faqs/clear/all")
async def clear_all_faqs(db: Session = Depends(get_db)):
    """Clear all FAQs from the system by marking them as inactive"""
    try:
        deleted_count = db.query(FAQDocument).filter(
            FAQDocument.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        
        # Reload FAQ dataset
        load_faq_dataset(db)
        
        logger.info(f"Cleared {deleted_count} FAQs from system")
        
        return {
            "success": True,
            "message": f"✅ Cleared {deleted_count} FAQs from system",
            "faqs_deleted": deleted_count,
            "total_faqs_remaining": len(FAQ_DATASET),
        }
    except Exception as e:
        logger.error(f"Error clearing FAQs: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing FAQs: {str(e)}")


@router.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    """Soft delete an FAQ (mark as inactive)"""
    faq = db.query(FAQDocument).filter(FAQDocument.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    faq.is_active = False
    db.commit()
    
    # Reload FAQ dataset
    load_faq_dataset(db)
    
    return {"success": True, "message": "FAQ deleted"}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages in a session"""
    session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "sender": m.sender,
            "content": m.content,
            "response_type": m.response_type,
            "confidence_score": m.confidence_score,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
