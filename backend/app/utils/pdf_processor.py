"""
PDF Processing and FAQ Extraction
Extracts FAQ content from PDF files and stores in database
"""

import os
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
import pypdf
import pdfplumber
from app.models.database import FAQDocument
from app.utils.embeddings import generate_embeddings

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    text_content = ""

    try:
        # Try using pdfplumber first (better for structured content)
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text_content += f"\n--- Page {page_num + 1} ---\n"
                text_content += page.extract_text() or ""

        if text_content.strip():
            return text_content

    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}, trying pypdf")

    try:
        # Fallback to pypdf
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            for page_num, page in enumerate(pdf_reader.pages):
                text_content += f"\n--- Page {page_num + 1} ---\n"
                text_content += page.extract_text()

        return text_content

    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise


def parse_faq_content(text: str) -> List[Tuple[str, str, str]]:
    """
    Parse FAQ content from extracted PDF text
    Looks for patterns like "Q:" "Question:" or numbered items
    
    Args:
        text: Extracted PDF text
        
    Returns:
        List of tuples: (question, answer, category)
    """
    faqs = []
    lines = text.split("\n")

    current_question = None
    current_answer = []
    current_category = "General"

    for i, line in enumerate(lines):
        line = line.strip()

        if not line:
            continue

        # Check for category markers
        if line.startswith("##") or line.startswith("Category:"):
            current_category = line.replace("##", "").replace("Category:", "").strip()
            continue

        # Check for question markers
        if (
            line.lower().startswith("q:")
            or line.lower().startswith("question:")
            or (line[0].isdigit() and ("." in line[:3] or ")" in line[:3]))
        ):
            # Save previous Q&A
            if current_question and current_answer:
                answer_text = " ".join(current_answer).strip()
                if answer_text:
                    faqs.append((current_question, answer_text, current_category))

            # Extract new question
            current_question = (
                line.replace("Q:", "")
                .replace("Question:", "")
                .replace("q:", "")
                .replace("question:", "")
            )
            # Remove numbering
            for j in range(len(current_question)):
                if current_question[j].isalpha():
                    current_question = current_question[j:].strip()
                    break

            current_answer = []

        # Check for answer markers
        elif (
            line.lower().startswith("a:")
            or line.lower().startswith("answer:")
        ):
            answer_text = (
                line.replace("A:", "")
                .replace("Answer:", "")
                .replace("a:", "")
                .replace("answer:", "")
                .strip()
            )
            if answer_text:
                current_answer.append(answer_text)

        # Continue building answer
        elif current_question:
            current_answer.append(line)

    # Save last Q&A
    if current_question and current_answer:
        answer_text = " ".join(current_answer).strip()
        if answer_text:
            faqs.append((current_question, answer_text, current_category))

    return faqs


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract keywords from text using simple heuristics
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction - words longer than 3 chars, not common words
    common_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "been", "be",
        "have", "has", "do", "does", "did", "will", "would", "could", "should",
        "can", "may", "might", "must", "shall", "if", "else", "this", "that",
        "which", "who", "what", "when", "where", "why", "how", "all", "each",
        "every", "both", "either", "neither", "some", "any", "no", "not"
    }

    words = text.lower().split()
    keywords = [
        word.strip(".,!?;:\"'")
        for word in words
        if len(word) > 3 and word.lower() not in common_words
    ]

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)

    return unique_keywords[:max_keywords]


def process_faq_pdf(
    pdf_path: str, db: Session, source_name: str = "uploaded_pdf"
) -> int:
    """
    Process a PDF file and store FAQs in database
    
    Args:
        pdf_path: Path to the PDF file
        db: Database session
        source_name: Name of the PDF source
        
    Returns:
        Number of FAQs stored
    """
    try:
        # Extract text from PDF
        logger.info(f"Extracting text from {pdf_path}")
        text_content = extract_text_from_pdf(pdf_path)

        # Parse FAQ content
        logger.info("Parsing FAQ content")
        faqs = parse_faq_content(text_content)

        if not faqs:
            logger.warning("No FAQs found in PDF")
            return 0

        # Store FAQs in database
        stored_count = 0
        for question, answer, category in faqs:
            if question and answer:
                try:
                    # Extract keywords
                    keywords = extract_keywords(f"{question} {answer}")

                    # Generate embeddings
                    embedding = generate_embeddings(f"{question} {answer}")

                    # Create FAQ document
                    faq_doc = FAQDocument(
                        question=question[:1000],  # Limit to 1000 chars
                        answer=answer[:5000],  # Limit to 5000 chars
                        category=category,
                        keywords=keywords,
                        embedding=embedding,
                        source=os.path.basename(pdf_path),
                        is_active=True,
                    )

                    db.add(faq_doc)
                    stored_count += 1

                except Exception as e:
                    logger.error(f"Error storing FAQ: {e}")
                    continue

        db.commit()
        logger.info(f"Stored {stored_count} FAQs in database")
        return stored_count

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        db.rollback()
        raise


def get_faq_by_id(faq_id: int, db: Session) -> Optional[FAQDocument]:
    """Get FAQ by ID"""
    return db.query(FAQDocument).filter(FAQDocument.id == faq_id).first()


def get_all_faqs(db: Session, active_only: bool = True) -> List[FAQDocument]:
    """Get all FAQs"""
    query = db.query(FAQDocument)
    if active_only:
        query = query.filter(FAQDocument.is_active == True)
    return query.all()


def search_faqs_by_keyword(keyword: str, db: Session) -> List[FAQDocument]:
    """
    Search FAQs by keyword
    """
    return (
        db.query(FAQDocument)
        .filter(
            (FAQDocument.keywords.contains([keyword]))
            | (FAQDocument.question.ilike(f"%{keyword}%"))
            | (FAQDocument.answer.ilike(f"%{keyword}%"))
        )
        .filter(FAQDocument.is_active == True)
        .all()
    )
