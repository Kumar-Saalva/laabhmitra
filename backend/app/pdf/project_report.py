"""Project report PDF (ReportLab). Every page carries the DRAFT watermark.

All figures come from engine/project_report.py. Rupees are written as "Rs." because the
built-in PDF fonts have no rupee sign.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.llm.templates import ACTIVITY_WORDS, NARRATIVE_SECTIONS
from app.money import format_inr
from app.pdf.pack import _safe, _watermark

DISCLAIMER = "Information only. Not affiliated with the Government of India."
GREY = colors.HexColor("#BBBBBB")


def rs(amount) -> str:
    return format_inr(amount, symbol="Rs. ")


def _table(rows, widths, total_row=False):
    table = Table(rows, colWidths=widths, repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, GREY),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if total_row:
        style.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
    table.setStyle(TableStyle(style))
    return table


def build_pdf(profile: dict, report: dict, narrative: dict) -> bytes:
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=11.5, textColor=colors.HexColor("#555555"))
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=20, alignment=0, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12.5, spaceBefore=12, spaceAfter=5)

    def para(text, style=body):
        return Paragraph(_safe(text), style)

    cost, finance, loan, years = report["cost_of_project"], report["means_of_finance"], report["loan"], report["years"]
    activity = ACTIVITY_WORDS.get(profile.get("business_activity"), "[fill in]")
    place = ", ".join(x for x in (profile.get("district"), profile.get("state")) if x) or "[fill in]"
    wide = [70 * mm] + [33 * mm] * 3

    story = [
        # Cover
        Spacer(1, 40 * mm),
        para("Project report", h1),
        para("DRAFT: review before use", ParagraphStyle("d", parent=h2, textColor=colors.HexColor("#A8321F"))),
        Spacer(1, 6 * mm),
        para(f"Proposed {activity} unit at {place}"),
        para("Prepared for an application under the Prime Minister's Employment Generation Programme (PMEGP)"),
        Spacer(1, 6 * mm),
        para("Name of applicant: [fill in]"),
        para("Name and address of the unit: [fill in]"),
        para("Bank and branch: [fill in]"),
        para("Date: [fill in]"),
        Spacer(1, 10 * mm),
        para("This draft was produced from figures entered by the applicant. The applicant must check every "
             "figure and complete every [fill in] before giving it to a bank or agency. " + DISCLAIMER, small),
        PageBreak(),

        # Summary
        para("Project summary", h2),
        _table([["Item", "Amount"],
                ["Total project cost", rs(cost["total"])],
                ["Bank loan requested", rs(finance["bank_loan"])],
                ["Own contribution", rs(finance["own_contribution"])],
                ["Estimated monthly instalment (EMI)", rs(loan["emi"])],
                ["Average DSCR over 3 years", f"{report['average_dscr']} ({report['band']})"]],
               [110 * mm, 55 * mm]),
        para(f"Loan terms assumed: {round(loan['annual_rate'] * 100, 2):g}% a year for {loan['tenure_months']} months. "
             "All profits are before tax.", small),

        para("Cost of project", h2),
        _table([["Item", "Amount"],
                ["Machinery and equipment", rs(cost["machinery"])],
                ["Building or civil work", rs(cost["building_or_civil"])],
                ["Working capital", rs(cost["working_capital"])],
                ["Total", rs(cost["total"])]], [110 * mm, 55 * mm], total_row=True),

        para("Means of finance", h2),
        _table([["Source", "Amount"],
                [f"Own contribution ({round(finance['own_contribution_rate'] * 100):g}% of project cost)", rs(finance["own_contribution"])],
                ["Bank loan", rs(finance["bank_loan"])],
                ["Total", rs(cost["total"])]], [110 * mm, 55 * mm], total_row=True),
        Spacer(1, 4),
        _table([["Shown separately", "Amount"], [Paragraph(_safe(finance["subsidy_label"]), body), rs(finance["subsidy_estimate"])]],
               [110 * mm, 55 * mm]),
        para("This report does not model how the bank adjusts the subsidy against the loan. "
             "The final subsidy is decided by the implementing agency.", small),

        para("Three-year projection (before tax)", h2),
        _table([["", *[f"Year {y['year']}" for y in years]],
                ["Sales", *[rs(y["sales"]) for y in years]],
                ["Raw material", *[rs(y["raw_material"]) for y in years]],
                ["Fixed costs (rent, wages, power etc.)", *[rs(y["fixed_costs"]) for y in years]],
                ["Depreciation", *[rs(y["depreciation"]) for y in years]],
                ["Interest on loan", *[rs(y["interest"]) for y in years]],
                ["Profit before tax", *[rs(y["profit_before_tax"]) for y in years]]], wide, total_row=True),

        para("Loan repayment schedule (yearly)", h2),
        _table([["Year", "Interest", "Principal repaid", "Loan left at year end"],
                *[[str(y["year"]), rs(y["interest"]), rs(y["principal"]), rs(y["closing_balance"])]
                  for y in report["loan_schedule"]]], [30 * mm, 45 * mm, 45 * mm, 45 * mm]),

        para("Debt service coverage ratio (DSCR)", h2),
        _table([["", *[f"Year {y['year']}" for y in years]],
                ["Cash accrual (profit before tax + depreciation)", *[rs(y["cash_accrual"]) for y in years]],
                ["Interest", *[rs(y["interest"]) for y in years]],
                ["Principal repaid", *[rs(y["principal_repaid"]) for y in years]],
                ["DSCR", *[str(y["dscr"]) if y["dscr"] is not None else "no repayment due" for y in years]]],
               wide, total_row=True),
        para(f"DSCR = (cash accrual + interest) / (principal repaid + interest). "
             f"Average over 3 years: {report['average_dscr']} ({report['band']}).", small),
        PageBreak(),

        para("Assumptions", h2),
        *[para(f"{n}. {text}") for n, text in enumerate(report["assumptions"], 1)],
    ]
    for key in NARRATIVE_SECTIONS:
        story += [para(narrative["titles"][key], h2), para(narrative["sections"][key])]
    story += [Spacer(1, 10), para(DISCLAIMER, small)]

    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                      bottomMargin=18 * mm, title="LaabhMitra project report (draft)"
                      ).build(story, onFirstPage=_watermark, onLaterPages=_watermark)
    return buffer.getvalue()
