"""Centralized application configuration - Environment variables only"""
from dataclasses import dataclass, field
from pathlib import Path
import os

@dataclass
class AppConfig:
    """Application configuration from environment variables"""
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    default_model: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
    max_slides: int = int(os.getenv("MAX_SLIDES", "50"))
    default_slides: int = int(os.getenv("DEFAULT_SLIDES", "10"))
    cache_dir: Path = Path(os.getenv("CACHE_DIR", ".cache"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def from_file(cls, path: str = None) -> "AppConfig":
        """Load config from environment variables"""
        return cls()
