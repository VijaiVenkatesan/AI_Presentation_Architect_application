"""
LLM Handler for Groq API
"""
import os
import logging
from typing import Optional, Dict, Any, List
import time

logger = logging.getLogger(__name__)

class LLMHandler:
    """Handle LLM interactions with Groq API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLM handler"""
        # Priority: explicit param > env var > secrets > None
        self.api_key = (
            api_key or 
            os.getenv("GROQ_API_KEY") or 
            ""
        )
        
        self.client = None
        self.default_model = "llama-3.3-70b-versatile"
        
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            logger.warning("GROQ_API_KEY not configured")
    
    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        return self.client is not None and self.api_key != ""
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate a text response from the LLM
        
        Args:
            prompt: The input prompt
            model: Model to use (default: llama-3.3-70b-versatile)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        
        Returns:
            Generated text or None if failed
        """
        if not self.is_configured():
            logger.error("LLM not configured")
            return None
        
        try:
            model = model or self.default_model
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI presentation assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            return None
    
    def generate_structured_response(
        self,
        prompt: str,
        response_format: Optional[Dict[str, str]] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a structured (JSON) response from the LLM
        
        Args:
            prompt: The input prompt
            response_format: Format specification (e.g., {"type": "json_object"})
            model: Model to use
            max_tokens: Maximum tokens in response
        
        Returns:
            Parsed JSON dict or None if failed
        """
        if not self.is_configured():
            logger.error("LLM not configured")
            return None
        
        try:
            model = model or self.default_model
            
            # Add JSON instruction to prompt
            json_prompt = f"""
            {prompt}
            
            IMPORTANT: Return ONLY valid JSON. No markdown, no explanations, just the JSON object.
            """
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a JSON API. Return only valid JSON objects."},
                    {"role": "user", "content": json_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3  # Lower temperature for more consistent JSON
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON
            import json
            # Clean up markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Structured LLM generation failed: {e}", exc_info=True)
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if not self.is_configured():
            return []
        
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return [self.default_model]
