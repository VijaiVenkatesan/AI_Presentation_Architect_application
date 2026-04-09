# 🏗️ Enterprise AI Presentation Architect

> **Generate stunning, template-perfect PowerPoint presentations powered by AI + real-time web research.**
> Finalized for 100% layout fidelity and strict corporate branding compliance.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://enterprise-ai-presentation-architect-app.streamlit.app/)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### ⚛️ Presentation Architecture
- **Gamma Atomizer (Slide Doubling)** — Logic-driven toggle to split dense slides into **Narrative + Visual** (Chart/Table) pairs, ensuring 0% layout overlap.
- **🛡️ Corporate Branding Guard** — Strict **2.2-inch top-margin** enforcement with floor detection to protect enterprise headers, logobars, and red bars.
- **🧠 Smart Layout Bifurcation**:
    - **Narrative Slides**: Automatically uses the template's native "Title and Content" layouts.
    - **Visual Insights**: Uses "Blank Layouts" for 100% sterile rendering of charts and tables.
- **🔄 Adaptive Batching** — Segments generation into **5-slide pause/resume cycles** to prevent AI model truncation and ensure 20+ slide consistency.
- **🖥️ 16:9 Widescreen Optimized** — Dynamic font scaling and space negotiation for modern corporate widescreen templates.

### Core Capabilities
- **Template-Faithful Generation** — Upload a PPTX template and generate new presentations that preserve 100% of the original styling.
- **AI Content Generation** — Powered by Groq API + Real-Time Web Research (DuckDuckGo).
- **Intelligent Visuals**: Automated generation of Bar, Column, Line charts and fully styled consulting Tables.
- **Notes & Subtitles**: Mandated consulting-grade subtitles and talking points for every slide.

### UI Features
- **⚛️ Gamma Atomizer Toggle**: Enable/Disable slide-doubling logic at runtime via the sidebar.
- **Live Progress Tracing**: Detailed status updates (Search → Generation → Atomization → Rendering).
- **Consulting Dark Theme**: Enterprise glassmorphism UI with slide preview cards.
- **PPTX + PDF Export**: Instant downloads with total layout fidelity.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Groq API key ([get one free](https://console.groq.com))

### Local Setup

```bash
# 1. Clone or navigate to project directory
cd AI_Presentation_Architecture_App

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
# Create .streamlit/secrets.toml and add:
# GROQ_API_KEY = "your-actual-groq-api-key"

# 5. Run the app
streamlit run app/main.py
```

---

## 📁 Project Structure

```
AI_Presentation_Architecture_App/
├── app/
│   └── main.py                  # Streamlit entry point + UI Logic
├── core/
│   ├── ppt_generator.py         # Advanced 16:9 Sterile Rendering Engine
│   ├── content_engine.py        # Groq AI + Adaptive Batching Logic
│   ├── template_parser.py       # PPTX/image branding analyzer
│   ├── search_engine.py         # DuckDuckGo research integrator
│   └── preview_engine.py        # Slide preview rendering
├── assets/
│   └── (User Uploaded Templates)
├── .streamlit/
│   ├── config.toml              # UI Theme & Branding
│   └── secrets.toml             # API Key Storage
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```

---

## 📊 Technical Architecture

- **Rendering Engine**: Uses `python-pptx` with a "Sterile Stacking" architecture (Title → Subtitle → Content → Visual).
- **Branding Guard**: Dynamic `safe_top` calculation (default 2.2") ensuring generated text NEVER overlaps with corporate red header bars.
- **Slide Atomizer**: Algorithm that detects combined Narrative + Visual slides and decomposes them into pairs to maximize visual density and legibility.
- **Adaptive Batching**: Logic that segments 20+ slide requests into smaller batches to circumvent model output truncation.

---

## 🛡️ License

MIT License — see [LICENSE](LICENSE) for details.
