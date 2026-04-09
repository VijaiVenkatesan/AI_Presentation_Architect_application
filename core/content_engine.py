"""
Enterprise AI Presentation Architect — Content Engine
Manages Groq API interaction, dynamic model fetching, and structured content generation.
"""

import json
import time
import logging
import re
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st

from core.search_engine import WebSearchEngine

logger = logging.getLogger("PresentationArchitect")

# ─── Constants ──────────────────────────────────────────────────────────────────

GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_MODELS_ENDPOINT = f"{GROQ_API_BASE}/models"
GROQ_CHAT_ENDPOINT = f"{GROQ_API_BASE}/chat/completions"
FALLBACK_MODEL = "llama3-70b-8192"
MODEL_CACHE_TTL = 3600  # 1 hour

# Models to exclude (audio, vision-only, deprecated, embedding)
EXCLUDED_MODEL_PATTERNS = [
    "whisper", "distil-whisper",
    "llava", "vision",
    "guard", "moderation",
    "embed", "embedding",
    "tts", "audio", "playai",
    "compound",
]

# ─── Content Engine ─────────────────────────────────────────────────────────────

class ContentEngine:
    """
    Manages AI content generation via Groq API.
    Handles dynamic model fetching, web search enrichment, and structured output.
    """

    def __init__(self):
        self.api_key = self._get_api_key()
        self.search_engine = WebSearchEngine()
        self._models_cache = None
        self._models_cache_time = 0

    def _get_api_key(self) -> str:
        """Retrieve Groq API key from Streamlit secrets or environment."""
        try:
            return st.secrets["GROQ_API_KEY"]
        except Exception:
            pass
        import os
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            logger.warning("No Groq API key found in secrets or environment")
        return key

    def _headers(self) -> Dict:
        """Build API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    # ─── Dynamic Model Fetching ─────────────────────────────────────────────

    def fetch_available_models(self, force_refresh: bool = False) -> List[Dict]:
        """
        Dynamically fetch available chat models from Groq API.
        Caches results for 1 hour. Falls back gracefully on failure.
        """
        now = time.time()

        # Return cached if valid
        if (not force_refresh
                and self._models_cache is not None
                and (now - self._models_cache_time) < MODEL_CACHE_TTL):
            return self._models_cache

        # Also check session state cache
        if (not force_refresh
                and st.session_state.get("available_models")
                and st.session_state.get("models_last_fetched", 0)
                and (now - st.session_state["models_last_fetched"]) < MODEL_CACHE_TTL):
            self._models_cache = st.session_state["available_models"]
            self._models_cache_time = st.session_state["models_last_fetched"]
            return self._models_cache

        if not self.api_key:
            logger.warning("No API key — returning fallback model")
            return self._fallback_models()

        try:
            response = requests.get(
                GROQ_MODELS_ENDPOINT,
                headers=self._headers(),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")

                # Skip excluded models
                if any(pattern in model_id.lower() for pattern in EXCLUDED_MODEL_PATTERNS):
                    continue

                # Only include active models
                if model.get("active") is False:
                    continue

                models.append({
                    "id": model_id,
                    "name": model_id,
                    "owned_by": model.get("owned_by", "unknown"),
                    "context_window": model.get("context_window", 8192),
                    "created": model.get("created", 0),
                })

            # Sort by name
            models.sort(key=lambda m: m["id"])

            if not models:
                logger.warning("No valid models found — using fallback")
                models = self._fallback_models()

            # Update caches
            self._models_cache = models
            self._models_cache_time = now
            st.session_state["available_models"] = models
            st.session_state["models_last_fetched"] = now

            logger.info(f"Fetched {len(models)} available models from Groq")
            return models

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch models from Groq API: {e}")
            return self._fallback_models()
        except Exception as e:
            logger.error(f"Unexpected error fetching models: {e}")
            return self._fallback_models()

    def _fallback_models(self) -> List[Dict]:
        """Return fallback model list when API is unavailable."""
        return [{
            "id": FALLBACK_MODEL,
            "name": FALLBACK_MODEL,
            "owned_by": "meta",
            "context_window": 8192,
            "created": 0,
        }]

    def get_model_names(self) -> List[str]:
        """Get list of available model IDs for UI dropdown."""
        models = self.fetch_available_models()
        return [m["id"] for m in models]

    def get_model_context_window(self, model_id: str) -> int:
        """Get context window size for a model."""
        models = self.fetch_available_models()
        for m in models:
            if m["id"] == model_id:
                return m.get("context_window", 8192)
        return 8192

    def _get_max_tokens(self, model_id: str, desired: int = 4096) -> int:
        """Determine safe max_tokens for a model, respecting its limits."""
        ctx_window = self.get_model_context_window(model_id)
        # Most Groq models cap max_tokens at a fraction of context_window.
        # Use at most 1/3 of context window, capped at the desired value,
        # and never exceed common Groq limits.
        safe_max = min(desired, ctx_window // 3, 4096)
        # Ensure at least a reasonable minimum
        return max(safe_max, 1024)

    # ─── Content Generation ─────────────────────────────────────────────────

    def generate_presentation_content(
        self,
        topic: str,
        slide_count: int,
        model_id: str,
        template_profile: Optional[Dict] = None,
        custom_instructions: str = "",
        progress_callback=None,
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Generate structured presentation content using Groq AI.

        Args:
            topic: Presentation topic/prompt
            slide_count: Number of slides to generate
            model_id: Groq model ID to use
            template_profile: Extracted template metadata
            custom_instructions: Additional user instructions
            progress_callback: Function to report progress (0.0-1.0)

        Returns:
            Tuple of (content_dict, error_message)
        """
        if not self.api_key:
            return None, "Groq API key not configured. Please add it to Streamlit secrets."

        if not topic.strip():
            return None, "Please provide a presentation topic."

        try:
            # Phase 1: Web research (10-30% progress)
            if progress_callback:
                progress_callback(0.1, "🔍 Researching topic online...")

            web_context = ""
            try:
                web_context = self.search_engine.search_for_topic(topic)
            except Exception as e:
                logger.warning(f"Web search failed (continuing without): {e}")

            if progress_callback:
                progress_callback(0.3, "🧠 Generating presentation content with AI...")

            # Phase 2: Build prompt and generate
            # Lowered threshold to 5 slides to prevent truncation on smaller models
            if slide_count <= 5:
                content, error = self._generate_batch(
                    topic, slide_count, model_id, template_profile,
                    custom_instructions, web_context, 1, slide_count,
                    progress_callback, 0.3, 0.9
                )
                if error:
                    return None, error
                return content, None
            else:
                # Batch generation for large slide counts
                all_slides = []
                batch_size = 5 # Reduced from 15 to 5 for model stability
                total_batches = (slide_count + batch_size - 1) // batch_size

                for batch_idx in range(total_batches):
                    start_slide = batch_idx * batch_size + 1
                    end_slide = min((batch_idx + 1) * batch_size, slide_count)
                    batch_count = end_slide - start_slide + 1

                    progress_start = 0.3 + (0.6 * batch_idx / total_batches)
                    progress_end = 0.3 + (0.6 * (batch_idx + 1) / total_batches)

                    if progress_callback:
                        progress_callback(
                            progress_start,
                            f"🧠 Generating slides {start_slide}-{end_slide} "
                            f"(batch {batch_idx + 1}/{total_batches})..."
                        )

                    batch_instructions = (
                        f"{custom_instructions}\n\n"
                        f"This is batch {batch_idx + 1} of {total_batches}. "
                        f"Generate slides {start_slide} through {end_slide}. "
                        f"Total presentation has {slide_count} slides. "
                        f"Maintain continuity with previous slides."
                    )

                    if batch_idx > 0 and all_slides:
                        # Provide context of previous slide titles
                        prev_titles = [s.get("title", "") for s in all_slides[-3:]]
                        batch_instructions += f"\nPrevious slide titles: {prev_titles}"

                    batch_content, error = self._generate_batch(
                        topic, batch_count, model_id, template_profile,
                        batch_instructions, web_context,
                        start_slide, end_slide,
                        progress_callback, progress_start, progress_end
                    )

                    if error:
                        # If a batch fails, try to continue with what we have
                        logger.error(f"Batch {batch_idx + 1} failed: {error}")
                        if not all_slides:
                            return None, error
                        # Generate placeholder slides for failed batch
                        for sn in range(start_slide, end_slide + 1):
                            all_slides.append({
                                "slide_number": sn,
                                "title": f"Slide {sn}",
                                "bullet_points": ["Content generation pending — please edit manually"],
                                "notes": ""
                            })
                        continue

                    if batch_content and "slides" in batch_content:
                        # Renumber slides
                        for j, slide in enumerate(batch_content["slides"]):
                            slide["slide_number"] = start_slide + j
                        all_slides.extend(batch_content["slides"])

                if progress_callback:
                    progress_callback(0.9, "✅ Content generation complete!")

                return {"slides": all_slides}, None

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return None, f"Content generation failed: {str(e)}"

    def _generate_batch(
        self, topic, slide_count, model_id, template_profile,
        custom_instructions, web_context, start_num, end_num,
        progress_callback, prog_start, prog_end
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Generate a batch of slides via Groq API."""

        system_prompt = self._build_system_prompt(
            slide_count, template_profile, start_num, end_num
        )
        user_prompt = self._build_user_prompt(
            topic, slide_count, web_context, custom_instructions, start_num, end_num
        )

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                max_tok = self._get_max_tokens(model_id, desired=4096)
                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": max_tok,
                    "response_format": {"type": "json_object"},
                }

                response = requests.post(
                    GROQ_CHAT_ENDPOINT,
                    headers=self._headers(),
                    json=payload,
                    timeout=120
                )

                if response.status_code == 429:
                    # Rate limited — wait and retry
                    retry_after = int(response.headers.get("retry-after", 5))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    if progress_callback:
                        progress_callback(prog_start, f"⏳ Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                content_str = data["choices"][0]["message"]["content"]
                content = self._parse_json_response(content_str)

                if content is None:
                    if attempt < max_retries - 1:
                        logger.warning(f"Failed to parse JSON (attempt {attempt + 1}), retrying...")
                        continue
                    return None, "Failed to parse AI response as valid JSON"

                # Validate
                if "slides" not in content:
                    content = {"slides": [content] if isinstance(content, dict) else content}

                if progress_callback:
                    progress_callback(prog_end, "✅ Batch generated successfully")

                return content, None

            except requests.exceptions.Timeout:
                logger.warning(f"Request timed out (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None, "Request timed out. Try reducing slide count or using a faster model."

            except requests.exceptions.RequestException as e:
                error_detail = ""
                try:
                    error_detail = e.response.json().get("error", {}).get("message", "")
                except Exception:
                    error_detail = str(e)
                logger.error(f"API request failed: {error_detail}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None, f"Groq API error: {error_detail}"

        return None, "Max retries exceeded"

    def _parse_json_response(self, content_str: str) -> Optional[Dict]:
        """Parse JSON from LLM response, handling various formats."""
        # Direct parse
        try:
            return json.loads(content_str)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code blocks
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}'
        ]
        for pattern in patterns:
            match = re.search(pattern, content_str)
            if match:
                try:
                    return json.loads(match.group(1) if '```' in pattern else match.group(0))
                except json.JSONDecodeError:
                    continue

        # Last resort: try to fix common issues
        try:
            # Remove trailing commas
            fixed = re.sub(r',\s*}', '}', content_str)
            fixed = re.sub(r',\s*]', ']', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        return None

    def _build_system_prompt(
        self, slide_count: int, template_profile: Optional[Dict],
        start_num: int, end_num: int
    ) -> str:
        """Build the system prompt for content generation."""
        template_context = ""
        if template_profile:
            layouts = template_profile.get("layouts", [])
            if layouts:
                layout_names = [l.get("name", "Unknown") for l in layouts[:10]]
                template_context = f"""
TEMPLATE INFORMATION:
- Available layouts: {layout_names}
- Number of layouts: {len(layouts)}
- Try to vary the layout_index (0-{len(layouts)-1}) across slides for visual diversity.
"""

        return f"""You are an expert presentation content architect. You create enterprise-grade, consulting-quality presentation content.

CRITICAL RULES:
1. Return ONLY valid JSON — no markdown, no commentary, no extra text.
2. Follow the exact JSON schema specified.
3. Content must be professional, data-driven, and actionable.
4. Use the consulting storytelling arc: Problem → Insight → Solution → Impact → Metrics.
5. Automatically decide when slides should include charts, tables, or diagrams.
6. Each content slide MUST have 3-5 high-value bullet points. Each bullet should be 10-20 words long, impactful, and professional. Avoid short, one-line bullets.
7. MANDATORY: You MUST include at least 3-4 visual data elements (chart_data or table_data) in every 20-slide presentation. Do not provide 'null' for everything.
8. Include quantitative data, percentages, and metrics where relevant.
9. Each slide title should be unique and compelling.
10. Notes should provide speaker talking points.
{template_context}

JSON SCHEMA (you must follow this exactly):
{{
  "slides": [
    {{
      "slide_number": <int>,
      "title": "<compelling slide title>",
      "subtitle": "<optional subtitle>",
      "bullet_points": ["<point1>", "<point2>", ...],
      "chart_data": {{
        "type": "bar|pie|line",
        "title": "<chart title>",
        "categories": ["<cat1>", "<cat2>", ...],
        "values": [<val1>, <val2>, ...]
      }} or null,
      "table_data": {{
        "headers": ["<col1>", "<col2>", ...],
        "rows": [["<val1>", "<val2>", ...], ...]
      }} or null,
      "diagram_type": "flow|process|architecture" or null,
      "image_prompt": "<descriptive prompt for slide image>" or null,
      "notes": "<speaker notes>",
      "layout_index": <int 0-based layout index>
    }}
  ]
}}

SMART CONTENT RULES:
- Slide 1: Always a title/cover slide
- Include at least 1 chart slide for every 5 slides
- Include at least 1 table slide for every 7 slides
- Use diagrams for process/architecture topics
- Final slide: Summary/conclusion with key takeaways or call to action
- Vary slide types for visual engagement"""

    def _build_user_prompt(
        self, topic: str, slide_count: int, web_context: str,
        custom_instructions: str, start_num: int, end_num: int
    ) -> str:
        """Build the user prompt with topic, research, and instructions."""
        prompt_parts = [
            f"Create a {slide_count}-slide enterprise presentation about: {topic}",
            f"\nSlide numbers should range from {start_num} to {end_num}.",
        ]

        if web_context:
            prompt_parts.append(f"\n{web_context}")

        if custom_instructions:
            prompt_parts.append(f"\nADDITIONAL INSTRUCTIONS:\n{custom_instructions}")

        prompt_parts.append(
            f"\nGenerate exactly {end_num - start_num + 1} slides. "
            "Return ONLY the JSON object with the 'slides' array. No other text."
        )

        return "\n".join(prompt_parts)

    # ─── Single Slide Regeneration ──────────────────────────────────────────

    def regenerate_single_slide(
        self, slide_number: int, topic: str, model_id: str,
        context_slides: List[Dict] = None, instructions: str = ""
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Regenerate content for a single slide.

        Args:
            slide_number: The slide number to regenerate
            topic: Overall presentation topic
            model_id: Model to use
            context_slides: Surrounding slides for context
            instructions: Specific instructions for this slide

        Returns:
            Tuple of (slide_dict, error_message)
        """
        if not self.api_key:
            return None, "Groq API key not configured."

        context = ""
        if context_slides:
            context = "Surrounding slide titles for context:\n"
            for s in context_slides:
                context += f"  - Slide {s.get('slide_number', '?')}: {s.get('title', '')}\n"

        system_prompt = """You are a presentation content expert. Generate content for a SINGLE slide.
Return ONLY valid JSON for ONE slide matching this schema:
{
  "slide_number": <int>,
  "title": "<title>",
  "subtitle": "<subtitle>",
  "bullet_points": ["<point1>", ...],
  "chart_data": null or {"type": "bar|pie|line", "title": "<title>", "categories": [...], "values": [...]},
  "table_data": null or {"headers": [...], "rows": [...]},
  "diagram_type": null or "flow|process|architecture",
  "image_prompt": null or "<prompt>",
  "notes": "<speaker notes>",
  "layout_index": 1
}"""

        user_prompt = (
            f"Regenerate slide {slide_number} for a presentation about: {topic}\n"
            f"{context}\n{instructions}\n"
            "Return ONLY the JSON object for this single slide."
        )

        try:
            max_tok = self._get_max_tokens(model_id, desired=2000)
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.8,
                "max_tokens": max_tok,
                "response_format": {"type": "json_object"},
            }

            response = requests.post(
                GROQ_CHAT_ENDPOINT,
                headers=self._headers(),
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            content_str = data["choices"][0]["message"]["content"]
            slide_data = self._parse_json_response(content_str)

            if slide_data is None:
                return None, "Failed to parse regenerated slide content"

            # If wrapped in slides array, extract first
            if "slides" in slide_data and isinstance(slide_data["slides"], list):
                slide_data = slide_data["slides"][0]

            slide_data["slide_number"] = slide_number
            return slide_data, None

        except Exception as e:
            logger.error(f"Slide regeneration failed: {e}")
            return None, f"Regeneration failed: {str(e)}"
