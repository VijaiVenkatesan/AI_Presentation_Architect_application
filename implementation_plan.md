# Enterprise AI Presentation Architect — Implementation Plan

## Overview

Build a production-grade Streamlit application that generates PowerPoint presentations matching uploaded templates exactly. The system uses **Groq AI** for content generation, **DuckDuckGo** for real-time web search, and **python-pptx** for template-faithful PPT generation.

**Target directory:** `d:\Antigravity_Projects\AI_Presentation_Architecture_App\`

---

## User Review Required

> [!IMPORTANT]
> **Groq API Key**: You'll need a valid Groq API key. The app will read it from Streamlit secrets (`secrets.toml`) or environment variable `GROQ_API_KEY`. Please confirm you have one.

> [!IMPORTANT]
> **Streamlit Cloud Deployment**: The plan targets Streamlit Cloud free tier. LibreOffice won't be available there for PDF export, so PDF export will use `fpdf2` + slide image rendering as a fallback. If you need native LibreOffice PDF conversion, a Docker deployment would be required.

> [!WARNING]
> **Image-based template parsing**: Full OCR-based layout reconstruction from slide images (OpenCV + Tesseract) is extremely complex for pixel-perfect replication. The implementation will extract text via OCR and infer basic layout regions, but won't achieve 100% fidelity from images alone. PPTX template upload will provide the best results.

---

## Architecture

```
AI_Presentation_Architecture_App/
├── app/
│   └── main.py                  # Streamlit entry point
├── core/
│   ├── __init__.py
│   ├── template_parser.py       # PPTX/image template analysis
│   ├── ppt_generator.py         # PPT generation engine
│   ├── content_engine.py        # Groq AI content generation
│   ├── search_engine.py         # DuckDuckGo web search
│   └── preview_engine.py        # Slide preview rendering
├── utils/
│   ├── __init__.py
│   └── helpers.py               # Shared utilities
├── assets/
│   └── sample_template.pptx     # Sample template (generated)
├── .streamlit/
│   └── secrets.toml.example     # Secrets template
├── requirements.txt
├── README.md
└── packages.txt                 # System deps for Streamlit Cloud
```

---

## Proposed Changes

### Component 1: Core — Template Parser

#### [NEW] [template_parser.py](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/core/template_parser.py)

Handles PPTX and image template analysis:

- **PPTX parsing** (`python-pptx`):
  - Extract all slide layouts from slide master
  - Map placeholder indices → positions, sizes, font specs
  - Extract color scheme from theme XML
  - Detect logos/images and their positions
  - Store chart/table styles if present
  - Return a `TemplateProfile` dataclass with all extracted metadata

- **Image parsing** (Pillow + pytesseract):
  - OCR text extraction from slide images
  - Basic region detection (header, body, footer zones)
  - Color palette extraction from image pixels
  - Return an `ImageTemplateProfile` with inferred layout

---

### Component 2: Core — Content Engine

#### [NEW] [content_engine.py](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/core/content_engine.py)

Handles Groq API interaction and content generation:

- **Dynamic model fetching**:
  - `GET https://api.groq.com/openai/v1/models`
  - Filter: active, chat-capable only (exclude `whisper`, `distil-whisper`, `llava`, deprecated)
  - Cache with TTL=1 hour using `st.cache_data(ttl=3600)`
  - Fallback: `llama3-70b-8192`

- **Content generation**:
  - Build structured prompt with template context + web search results
  - Request JSON-formatted slide content
  - Parse and validate response against expected schema
  - Smart content rules: auto-detect chart/table/diagram needs based on topic

- **Prompt engineering**:
  - Consulting-style storytelling: Problem → Solution → Impact → Metrics
  - Include template layout info so AI knows placeholder count
  - Enforce structured JSON output format

---

### Component 3: Core — Search Engine

#### [NEW] [search_engine.py](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/core/search_engine.py)

Real-time web search integration:

- Use `duckduckgo-search` library (`DDGS`)
- Perform topic search with `max_results=8`
- Extract titles, snippets, URLs
- Format results as context string for LLM prompt injection
- Error handling with graceful fallback (empty context)
- Rate limiting protection

---

### Component 4: Core — PPT Generator

#### [NEW] [ppt_generator.py](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/core/ppt_generator.py)

The critical core engine:

- **Template-based generation**:
  - Load uploaded PPTX as base presentation
  - For each slide in generated content:
    - Select best-matching layout from template
    - Add slide using that layout
    - Populate placeholders with generated text
    - Preserve all formatting (font, size, color, alignment)
  - Deep-copy approach for complex shapes

- **Chart insertion**:
  - Create charts using `python-pptx` chart API
  - Match chart style to template's theme colors
  - Support: Bar, Pie, Line chart types

- **Table insertion**:
  - Create tables with template-matching styles
  - Apply header formatting, alternating rows

- **Image/logo handling**:
  - Copy logo positions from template
  - Insert generated images if `image_prompt` provided

- **From-scratch generation** (no template):
  - Create clean, professional default layout
  - Apply enterprise-grade styling

---

### Component 5: Core — Preview Engine

#### [NEW] [preview_engine.py](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/core/preview_engine.py)

Slide preview rendering for Streamlit UI:

- Convert PPTX slides to images using `python-pptx` + `Pillow`
  - Extract shapes and render them onto a Pillow canvas
  - Render text, shapes, backgrounds
- Generate thumbnail grid
- Full-size preview for selected slide
- Fallback: Display slide content as formatted HTML cards

---

### Component 6: Utils

#### [NEW] [helpers.py](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/utils/helpers.py)

Shared utilities:

- File I/O helpers (save/load temp files)
- Session state management (save/load/reset)
- Color conversion utilities (hex ↔ RGB ↔ RGBColor)
- Validation functions
- Logging configuration

---

### Component 7: Streamlit App

#### [NEW] [main.py](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/app/main.py)

Main Streamlit application with enterprise UI:

**Sidebar:**
- Template upload (PPTX / PNG / JPEG) with file uploader
- Slide count slider (1-50)
- Dynamic model selector dropdown (fetched from Groq)
- AI generation toggle (ON/OFF)
- Reset button
- Session save/load

**Main Panel:**
- Topic/prompt input text area
- Manual content editor (expandable per-slide)
- Live slide preview window (scrollable thumbnails)
- Slide reorder controls (move up/down)
- Individual slide regeneration buttons

**Bottom Section:**
- Generate Presentation button (primary CTA)
- Download PPTX button
- Download PDF button
- Progress bar during generation

**UI Design:**
- Custom CSS for enterprise look (dark sidebar, clean cards)
- Status indicators and progress feedback
- Error handling with user-friendly messages

---

### Component 8: Configuration & Deployment

#### [NEW] [requirements.txt](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/requirements.txt)

```
streamlit>=1.30.0
python-pptx>=0.6.23
Pillow>=10.0.0
requests>=2.31.0
duckduckgo-search>=4.0
pytesseract>=0.3.10
fpdf2>=2.7.0
```

#### [NEW] [packages.txt](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/packages.txt)

System dependencies for Streamlit Cloud:
```
tesseract-ocr
libtesseract-dev
```

#### [NEW] [secrets.toml.example](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/.streamlit/secrets.toml.example)

```toml
GROQ_API_KEY = "your-groq-api-key-here"
```

#### [NEW] [README.md](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/README.md)

Setup instructions, features list, deployment guide.

#### [NEW] [sample_template.pptx](file:///d:/Antigravity_Projects/AI_Presentation_Architecture_App/assets/sample_template.pptx)

Generated programmatically via python-pptx with professional styling.

---

## Open Questions

> [!IMPORTANT]
> 1. **Groq API Key**: Do you already have a Groq API key, or should I include instructions for obtaining one?

> [!IMPORTANT]
> 2. **PDF Export**: On Streamlit Cloud, LibreOffice is not available. I'll implement PDF export using slide-to-image conversion + `fpdf2`. Is this acceptable, or do you need native PDF fidelity?

> [!NOTE]
> 3. **Tesseract OCR**: For image-based template parsing, Tesseract must be installed. On Streamlit Cloud this is handled via `packages.txt`. For local development on Windows, you may need to install Tesseract separately. Should I include Windows setup instructions?

---

## Verification Plan

### Automated Tests
1. **Local run test**: `streamlit run app/main.py` — verify UI loads without errors
2. **Template parsing test**: Upload sample PPTX → verify layout extraction
3. **Content generation test**: Enter topic with AI ON → verify structured JSON output
4. **PPT generation test**: Generate full presentation → verify PPTX opens correctly in PowerPoint
5. **Preview test**: Verify slide previews render in UI

### Manual Verification
1. Upload the sample template and generate a presentation
2. Compare generated PPTX with original template styling
3. Test all UI controls (slider, model selector, toggle, reset)
4. Test download buttons (PPTX and PDF)
5. Test slide editing and reordering features
6. Record a browser walkthrough of the complete flow
