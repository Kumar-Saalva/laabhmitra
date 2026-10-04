"""Application Pack: document checklist (have / need) and a ReportLab PDF.

The PDF is in English and writes rupees as "Rs." because the built-in PDF fonts
have no rupee sign and cannot shape Kannada or Devanagari text.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DISCLAIMER = ("Information only. Not affiliated with the Government of India. "
              "Final decisions are made by the implementing agency.")

# Words in a document name -> the profile boolean that tells us whether the merchant has it.
DOCUMENT_FIELDS = [
    ("udyam certificate", "udyam_registered"),
    ("vending certificate", "has_vending_proof"),
    ("education certificate", "education_8th_pass"),
    ("gstin", "gst_registered"),
    ("pan", "pan_available"),
    ("bank", "bank_account"),
]


def checklist(profile: dict, scheme: dict) -> list:
    """[{document, state: have|need|check, note}] from the profile booleans.

    'check' means we have not asked about it, so the merchant should confirm."""
    items = []
    for doc in scheme.get("documents", []):
        lowered = doc.lower()
        words = lowered.replace("(", " ").replace(")", " ").replace("/", " ").split()
        state = "check"
        for key, field in DOCUMENT_FIELDS:
            matched = key in lowered if " " in key else key in words
            if matched and profile.get(field) is not None:
                state = "have" if profile[field] else "need"
                break
        note = None
        if "(if" in lowered:
            note = "Needed only if this applies to you: " + doc[doc.index("(") + 1:].rstrip(")")
        items.append({"document": doc, "state": state, "note": note})
    return items


def _safe(text: str) -> str:
    """Make text printable with the standard PDF fonts and safe inside a Paragraph."""
    text = text.replace("₹", "Rs. ").replace("→", "->").replace("✓", "").replace("✗", "")
    text = text.encode("latin-1", "replace").decode("latin-1")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _watermark(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 44)
    canvas.setFillColor(colors.Color(0.75, 0.15, 0.1, alpha=0.13))
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "DRAFT: review before use")
    canvas.restoreState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(A4[0] / 2, 10 * mm, DISCLAIMER)


def build_pdf(profile: dict, scheme: dict, result: dict, draft_text: str, items: list) -> bytes:
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#555555"))
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=17, alignment=0, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)

    story = [
        Paragraph(_safe(f"Application pack: {scheme['short_name']}"), h1),
        Paragraph(_safe(scheme["name"]), small),
        Paragraph(_safe(f"Readiness: {result['status'].replace('_', ' ').title()}; criteria met "
                        f"{result['met']} of {result['total']} ({result['unknown']} unknown). "
                        f"Rules last verified {scheme['last_verified']}."), small),
        Paragraph("Documents", h2),
    ]
    marks = {"have": "Have", "need": "Still need", "check": "Please confirm"}
    rows = [["", "Document", "Status"]] + [
        ["[x]" if i["state"] == "have" else "[ ]",
         Paragraph(_safe(i["document"]) + (f"<br/><font size=8 color='#666666'>{_safe(i['note'])}</font>" if i["note"] else ""), body),
         marks[i["state"]]] for i in items]
    if len(rows) > 1:
        table = Table(rows, colWidths=[10 * mm, 115 * mm, 35 * mm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No document list is available for this scheme yet.", body))

    story.append(Paragraph("How to apply", h2))
    app = scheme["application"]
    story.append(Paragraph(_safe(f"Channel: {app.get('channel') or 'Not yet available'}"), body))
    if app.get("url"):
        story.append(Paragraph(_safe(f"Official link: {app['url']}"), body))
    for n, step in enumerate(app.get("steps", []), 1):
        story.append(Paragraph(_safe(f"{n}. {step}"), body))
    story.append(Paragraph("You apply yourself on the official channel. This app never submits anything "
                           "or logs in for you.", small))

    story.append(Paragraph("Draft cover note", h2))
    for line in draft_text.split("\n"):
        story.append(Paragraph(_safe(line).replace("  ", "&nbsp;&nbsp;"), body) if line.strip() else Spacer(1, 5))

    story.append(Spacer(1, 8))
    story.append(Paragraph(_safe(f"Source: {scheme['sources'][0]['title']} ({scheme['sources'][0]['url']})"), small))

    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                      bottomMargin=18 * mm, title=f"LaabhMitra application pack: {scheme['short_name']}"
                      ).build(story, onFirstPage=_watermark, onLaterPages=_watermark)
    return buffer.getvalue()
