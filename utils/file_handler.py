"""File handling utilities - No circular imports"""
import tempfile
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_template_file(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        temp_dir = Path(tempfile.gettempdir()) / 'ppt_templates'
        temp_dir.mkdir(exist_ok=True)
        template_path = temp_dir / f"template_{int(time.time())}.pptx"
        with open(template_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        logger.info(f"Template saved to: {template_path}")
        return str(template_path)
    except Exception as e:
        logger.error(f"Failed to save template: {e}")
        return None
