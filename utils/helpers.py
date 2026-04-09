"""
Enterprise AI Presentation Architect — Shared Utilities
Provides session management, color conversion, file I/O, validation, and logging.
"""

import os
import io
import json
import time
import logging
import hashlib
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

import streamlit as st
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# ─── Logging ────────────────────────────────────────────────────────────────────

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return application logger."""
    logger = logging.getLogger("PresentationArchitect")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger

logger = setup_logging()

# ─── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class SlideContent:
    """Represents generated content for a single slide."""
    slide_number: int = 1
    title: str = ""
    subtitle: str = ""
    bullet_points: List[str] = field(default_factory=list)
    chart_data: Optional[Dict] = None
    table_data: Optional[Dict] = None
    diagram_type: Optional[str] = None
    image_prompt: Optional[str] = None
    notes: str = ""
    layout_index: int = 1  # Which template layout to use

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SlideContent":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TemplateProfile:
    """Stores extracted template metadata."""
    source_type: str = "pptx"  # "pptx" or "image"
    slide_width: int = 12192000  # EMU (default 13.33 inches)
    slide_height: int = 6858000  # EMU (default 7.5 inches)
    layouts: List[Dict] = field(default_factory=list)
    color_scheme: Dict[str, str] = field(default_factory=dict)
    fonts: Dict[str, str] = field(default_factory=dict)
    logo_info: Optional[Dict] = None
    background_color: Optional[str] = None
    placeholder_map: Dict[int, List[Dict]] = field(default_factory=dict)
    total_slides: int = 0
    theme_name: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "TemplateProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ─── Color Utilities ────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (0, 0, 0)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_pptx_color(hex_color: str) -> RGBColor:
    """Convert hex color to python-pptx RGBColor."""
    r, g, b = hex_to_rgb(hex_color)
    return RGBColor(r, g, b)


def pptx_color_to_hex(color: RGBColor) -> str:
    """Convert python-pptx RGBColor to hex string."""
    try:
        return rgb_to_hex(color[0], color[1], color[2])
    except (TypeError, IndexError):
        return "#000000"


# ─── File I/O ───────────────────────────────────────────────────────────────────

def save_temp_file(content: bytes, suffix: str = ".pptx", prefix: str = "ppt_") -> str:
    """Save bytes content to a temporary file and return the path."""
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix)
        tmp.write(content)
        tmp.close()
        logger.debug(f"Saved temp file: {tmp.name}")
        return tmp.name
    except Exception as e:
        logger.error(f"Failed to save temp file: {e}")
        raise


def cleanup_temp_files(paths: List[str]):
    """Remove temporary files safely."""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
                logger.debug(f"Cleaned up: {path}")
        except Exception as e:
            logger.warning(f"Failed to clean up {path}: {e}")


def get_file_hash(content: bytes) -> str:
    """Generate SHA256 hash of file content for caching."""
    return hashlib.sha256(content).hexdigest()[:16]


# ─── Session State Management ───────────────────────────────────────────────────

DEFAULT_SESSION_STATE = {
    "slides_content": [],
    "template_profile": None,
    "template_bytes": None,
    "template_filename": None,
    "generated_pptx": None,
    "generation_status": "idle",  # idle, generating, complete, error
    "error_message": None,
    "selected_model": None,
    "ai_enabled": True,
    "slide_count": 10,
    "topic": "",
    "edit_mode": False,
    "preview_images": [],
    "session_saved": False,
    "generation_progress": 0.0,
    "available_models": [],
    "models_last_fetched": 0,
}


def init_session_state():
    """Initialize all session state variables with defaults."""
    for key, default_value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def reset_session_state():
    """Reset session state to defaults, clearing all generated content."""
    # Clean up temp files
    if st.session_state.get("generated_pptx"):
        cleanup_temp_files([st.session_state["generated_pptx"]])

    for key, default_value in DEFAULT_SESSION_STATE.items():
        st.session_state[key] = default_value
    logger.info("Session state reset")


def save_session_to_json() -> str:
    """Export current session state to JSON string."""
    try:
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "slides_content": [
                s.to_dict() if isinstance(s, SlideContent) else s
                for s in st.session_state.get("slides_content", [])
            ],
            "template_profile": (
                st.session_state["template_profile"].to_dict()
                if st.session_state.get("template_profile")
                and isinstance(st.session_state["template_profile"], TemplateProfile)
                else st.session_state.get("template_profile")
            ),
            "slide_count": st.session_state.get("slide_count", 10),
            "topic": st.session_state.get("topic", ""),
            "selected_model": st.session_state.get("selected_model"),
            "ai_enabled": st.session_state.get("ai_enabled", True),
        }
        return json.dumps(export_data, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save session: {e}")
        return json.dumps({"error": str(e)})


def load_session_from_json(json_str: str) -> bool:
    """Import session state from JSON string."""
    try:
        data = json.loads(json_str)
        if "slides_content" in data:
            st.session_state["slides_content"] = [
                SlideContent.from_dict(s) if isinstance(s, dict) else s
                for s in data["slides_content"]
            ]
        if "template_profile" in data and data["template_profile"]:
            st.session_state["template_profile"] = TemplateProfile.from_dict(
                data["template_profile"]
            )
        for key in ["slide_count", "topic", "selected_model", "ai_enabled"]:
            if key in data:
                st.session_state[key] = data[key]
        logger.info("Session loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        return False


# ─── Validation ─────────────────────────────────────────────────────────────────

def validate_pptx_file(file_bytes: bytes) -> bool:
    """Check if the uploaded file is a valid PPTX."""
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(file_bytes))
        _ = len(prs.slides)
        return True
    except Exception:
        return False


def validate_image_file(file_bytes: bytes) -> bool:
    """Check if the uploaded file is a valid image."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
        return True
    except Exception:
        return False


def validate_slide_content(content: Dict) -> Tuple[bool, str]:
    """Validate generated slide content structure."""
    if not isinstance(content, dict):
        return False, "Content must be a dictionary"
    if "slides" not in content:
        return False, "Missing 'slides' key in content"
    if not isinstance(content["slides"], list):
        return False, "'slides' must be a list"
    if len(content["slides"]) == 0:
        return False, "No slides in content"
    for i, slide in enumerate(content["slides"]):
        if not isinstance(slide, dict):
            return False, f"Slide {i+1} is not a dictionary"
        if "title" not in slide:
            return False, f"Slide {i+1} missing 'title'"
    return True, "Valid"


# ─── Formatting Helpers ─────────────────────────────────────────────────────────

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def sanitize_filename(name: str) -> str:
    """Sanitize string for use as filename."""
    import re
    sanitized = re.sub(r'[^\w\s\-.]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:100] or "presentation"


def get_timestamp_str() -> str:
    """Get formatted timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
