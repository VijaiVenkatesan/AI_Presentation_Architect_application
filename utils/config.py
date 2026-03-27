"""Centralized application configuration - No YAML dependency"""
from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Optional

@dataclass
class AppConfig:
    """Application configuration with env var and secrets support"""
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    default_model: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
    max_slides: int = int(os.getenv("MAX_SLIDES", "50"))
    default_slides: int = int(os.getenv("DEFAULT_SLIDES", "10"))
    cache_dir: Path = Path(os.getenv("CACHE_DIR", ".cache"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def from_file(cls, path: str = "config.yaml") -> "AppConfig":
        """
        Load config from environment variables and Streamlit secrets
        YAML support is optional and disabled by default
        """
        # Try to import yaml, but don't fail if not available
        yaml_config = {}
        try:
            import yaml
            config_path = Path(path)
            if config_path.exists():
                with open(config_path) as f:
                    yaml_config = yaml.safe_load(f) or {}
        except ImportError:
            pass  # YAML not available, use env vars only
        except Exception:
            pass  # Any other error, use env vars only
        
        # Try to get from Streamlit secrets
        try:
            import streamlit as st
            secrets_key = st.secrets.get("GROQ_API_KEY", "")
        except:
            secrets_key = ""
        
        # Priority: Env var > Secrets > YAML > Defaults
        groq_key = (
            os.getenv("GROQ_API_KEY") or 
            secrets_key or 
            yaml_config.get("groq_api_key", "")
        )
        
        return cls(
            groq_api_key=groq_key,
            default_model=os.getenv("DEFAULT_MODEL", yaml_config.get("default_model", cls.default_model)),
            max_slides=int(os.getenv("MAX_SLIDES", yaml_config.get("max_slides", cls.max_slides))),
            default_slides=int(os.getenv("DEFAULT_SLIDES", yaml_config.get("default_slides", cls.default_slides))),
            cache_dir=Path(os.getenv("CACHE_DIR", yaml_config.get("cache_dir", cls.cache_dir))),
            log_level=os.getenv("LOG_LEVEL", yaml_config.get("log_level", cls.log_level)),
        )
