import json
import re

def safe_json_load(text):
    try:
        return json.loads(text)
    except:
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
    return {"slides": []}

def ensure_slide_structure(data):
    slides = data.get("slides", [])
    cleaned = []

    for slide in slides:
        cleaned.append({
            "title": slide.get("title", ""),
            "bullet_points": slide.get("bullet_points", []),
            "diagram_type": slide.get("diagram_type", ""),
            "image_prompt": slide.get("image_prompt", "")
        })

    return {"slides": cleaned}

def validate_slide_count(data, max_slides=100):
    return {"slides": data.get("slides", [])[:max_slides]}
