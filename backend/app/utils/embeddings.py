"""
Embeddings and Semantic Search
Generates embeddings for FAQs and performs semantic similarity matching
"""

import logging
from typing import List, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.models.database import FAQDocument

logger = logging.getLogger(__name__)

# Load sentence transformer model (lightweight, good for CPU)
MODEL_NAME = "all-MiniLM-L6-v2"  # ~22MB, fast, good quality
embedder = None


def get_embedder():
    """Lazy load the sentence transformer model"""
    global embedder
    if embedder is None:
        logger.info(f"Loading sentence transformer model: {MODEL_NAME}")
        embedder = SentenceTransformer(MODEL_NAME)
    return embedder


def generate_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for text
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector as list
    """
    try:
        embedder = get_embedder()
        embedding = embedder.encode(text, convert_to_numpy=False)
        return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return [0.0] * 384  # Return zero vector on error


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        vec1 = np.array(vec1, dtype=np.float32)
        vec2 = np.array(vec2, dtype=np.float32)

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(max(0.0, min(1.0, similarity)))
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0


def search_similar_faqs(
    query: str,
    db: Session,
    top_k: int = 5,
    min_similarity: float = 0.3,
) -> List[Tuple[FAQDocument, float]]:
    """
    Search for similar FAQs using semantic similarity
    
    Args:
        query: Query text
        db: Database session
        top_k: Number of top results to return
        min_similarity: Minimum similarity threshold
        
    Returns:
        List of tuples (FAQ, similarity_score)
    """
    try:
        # Generate query embedding
        query_embedding = generate_embeddings(query)

        # Get all active FAQs
        faqs = db.query(FAQDocument).filter(FAQDocument.is_active == True).all()

        # Calculate similarities
        similarities = []
        for faq in faqs:
            if faq.embedding:
                try:
                    similarity = cosine_similarity(query_embedding, faq.embedding)
                    if similarity >= min_similarity:
                        similarities.append((faq, similarity))
                except Exception as e:
                    logger.warning(f"Error calculating similarity for FAQ {faq.id}: {e}")
                    continue

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    except Exception as e:
        logger.error(f"Error searching similar FAQs: {e}")
        return []


def get_faq_context(
    query: str,
    db: Session,
    top_k: int = 3,
    min_similarity: float = 0.3,
) -> Tuple[str, List[int], float]:
    """
    Get FAQ context for a query
    
    Args:
        query: User query
        db: Database session
        top_k: Number of FAQs to retrieve
        min_similarity: Minimum similarity threshold
        
    Returns:
        Tuple of (context_text, faq_ids, average_confidence)
    """
    try:
        similar_faqs = search_similar_faqs(query, db, top_k, min_similarity)

        if not similar_faqs:
            return "", [], 0.0

        context_parts = []
        faq_ids = []
        similarities = []

        for faq, similarity in similar_faqs:
            context_parts.append(f"Q: {faq.question}\nA: {faq.answer}")
            faq_ids.append(faq.id)
            similarities.append(similarity)

        context_text = "\n\n---\n\n".join(context_parts)
        average_confidence = np.mean(similarities) if similarities else 0.0

        return context_text, faq_ids, float(average_confidence)

    except Exception as e:
        logger.error(f"Error getting FAQ context: {e}")
        return "", [], 0.0


def rerank_faqs(
    query: str,
    faqs: List[FAQDocument],
    top_k: int = 5,
) -> List[Tuple[FAQDocument, float]]:
    """
    Re-rank FAQs based on semantic similarity to query
    
    Args:
        query: Query text
        faqs: List of FAQ documents to re-rank
        top_k: Number of results to return
        
    Returns:
        List of tuples (FAQ, similarity_score)
    """
    try:
        query_embedding = generate_embeddings(query)

        ranked = []
        for faq in faqs:
            if faq.embedding:
                similarity = cosine_similarity(query_embedding, faq.embedding)
                ranked.append((faq, similarity))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    except Exception as e:
        logger.error(f"Error re-ranking FAQs: {e}")
        return [(faq, 0.5) for faq in faqs[:top_k]]
