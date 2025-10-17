"""
LLM Integration Module
Uses OpenRouter API for GPT-OSS 20B Free Model
"""

import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import httpx
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Generate response from the LLM"""
        pass

    @abstractmethod
    async def extract_confidence(
        self,
        query: str,
        context: str,
    ) -> float:
        """Extract confidence score for a response"""
        pass


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider for GPT-OSS 20B Free model"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.api_url = os.getenv(
            "OPENROUTER_BASE_URL", 
            "https://openrouter.ai/api/v1"
        ) + "/chat/completions"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        logger.info(f"Using OpenRouter API with model: {self.model}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Generate response using OpenRouter API"""
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/ai-customer-support-bot",
            "X-Title": "AI Customer Support Bot",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url, json=payload, headers=headers
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise

    async def extract_confidence(
        self,
        query: str,
        context: str,
    ) -> float:
        """Extract confidence score using OpenRouter"""
        prompt = f"""
Given the following customer query and the response provided, rate the confidence of the response on a scale of 0 to 1, where:
- 0 means the response is completely unrelated to the query
- 1 means the response perfectly answers the query

Query: {query}
Response: {context}

Provide only a number between 0 and 1.
        """

        response = await self.generate_response(
            prompt, temperature=0.3, max_tokens=10
        )

        try:
            confidence = float(response.strip())
            return max(0, min(1, confidence))
        except ValueError:
            return 0.5


class LLMManager:
    """Manager to handle LLM provider (OpenRouter only)"""

    def __init__(self):
        self.provider = self._initialize_provider()

    def _initialize_provider(self) -> LLMProvider:
        """Initialize OpenRouter provider"""
        return OpenRouterProvider()

    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Generate response from LLM"""
        try:
            return await self.provider.generate_response(
                prompt, system_message, temperature, max_tokens
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def extract_confidence(
        self,
        query: str,
        context: str,
    ) -> float:
        """Extract confidence score from LLM"""
        try:
            return await self.provider.extract_confidence(query, context)
        except Exception as e:
            logger.error(f"Error extracting confidence: {e}")
            return 0.5  # Default to medium confidence on error


# Global LLM manager instance
llm_manager = LLMManager()
