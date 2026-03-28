from reportlab.pdfgen import canvas
import json

def export_pdf(content_json, output="output.pdf"):
    data = json.loads(content_json)
    c = canvas.Canvas(output)

    y = 800
    for slide in data["slides"]:
        c.drawString(50, y, slide["title"])
        y -= 20

        for b in slide["bullet_points"]:
            c.drawString(70, y, "- " + b)
            y -= 15

        y -= 20
        if y < 100:
            c.showPage()
            y = 800

    c.save()
    return output
