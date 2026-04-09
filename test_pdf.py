from fpdf import FPDF
import textwrap

slides_data = [
    {
        "title": "Artificial Intelligence in Healthcare 2025",
        "subtitle": "Trends, innovations and latest developments",
        "bullet_points": [
            "Agentic AI integrates systems continuously for real-time monitoring",
            "Long word test: " + "A" * 150,
            "Bullet 3 with some text here."
        ],
        "notes": "Speaker notes here."
    }
]

pdf = FPDF(orientation='L', unit='mm', format='A4')
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(15, 15, 15)

def safe_str(txt):
    cleaned = str(txt).encode("latin-1", "replace").decode("latin-1")
    words = cleaned.split(" ")
    broken_words = [textwrap.fill(w, 80) if len(w) > 80 else w for w in words]
    return " ".join(broken_words)

for i, slide in enumerate(slides_data):
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(0, 20, safe_str(slide.get("title", f"Slide {i+1}")), ln=True, align='C')
    pdf.set_font('Helvetica', '', 14)
    if slide.get("subtitle"):
        pdf.cell(0, 12, safe_str(slide["subtitle"]), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 12)
    for bp in slide.get("bullet_points", []):
        pdf.multi_cell(0, 8, safe_str(f"  -  {bp}"))
    if slide.get("notes"):
        pdf.ln(5)
        pdf.set_font('Helvetica', 'I', 10)
        pdf.multi_cell(0, 7, safe_str(f"Notes: {slide['notes']}"))

pdf.output("test_export.pdf")
print("SUCCESS!")
