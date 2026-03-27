"""LLM Handler for Groq API - Improved JSON parsing"""
import os, logging, json, re
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or ""
        self.client = None
        self.default_model = "llama-3.3-70b-versatile"
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized")
            except Exception as e:
                logger.error(f"Groq init failed: {e}")
    
    def is_configured(self) -> bool:
        return self.client is not None and bool(self.api_key)
    
    def generate_response(self, prompt: str, model: Optional[str] = None, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        if not self.is_configured():
            return None
        try:
            resp = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[
                    {"role": "system", "content": "You are a helpful presentation assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None
    
    def generate_structured_response(self, prompt: str, response_format: Optional[Dict] = None, model: Optional[str] = None, max_tokens: int = 2000) -> Optional[Dict[str, Any]]:
        if not self.is_configured():
            return None
        try:
            # Enhanced prompt for JSON
            jp = f"""{prompt}

IMPORTANT: Return ONLY valid JSON. No markdown code blocks. No explanations. Just the JSON object or array."""
            
            resp = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[
                    {"role": "system", "content": "You are a JSON API. Return only valid JSON objects or arrays. No markdown, no text outside JSON."},
                    {"role": "user", "content": jp}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            content = resp.choices[0].message.content.strip()
            
            # Clean up markdown if present
            content = re.sub(r'^```json\s*', '', content, flags=re.IGNORECASE)
            content = re.sub(r'^```\s*', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\s*```$', '', content, flags=re.IGNORECASE)
            content = content.strip()
            
            # Try to parse JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as je:
                logger.warning(f"JSON parse error: {je}")
                # Try to extract JSON from text
                json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', content)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                logger.error(f"Could not extract JSON from: {content[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Structured LLM error: {e}", exc_info=True)
            return None
    
    def get_available_models(self) -> List[str]:
        if not self.is_configured():
            return []
        try:
            return [m.id for m in self.client.models.list().data]
        except:
            return [self.default_model]
