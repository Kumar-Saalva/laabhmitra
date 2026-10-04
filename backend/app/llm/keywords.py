"""Mock profile extraction: a keyword and regex reader. No network, no model.

It understands the three demo persona sentences (and close variations) in English,
plus the most common Kannada and Hindi words. Anything it is not sure of is left out,
so the engine treats it as UNKNOWN and the chat asks about it.
"""
import re

UNITS = {
    "crore": 10_000_000, "cr": 10_000_000, "ಕೋಟಿ": 10_000_000, "करोड़": 10_000_000,
    "lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000, "ಲಕ್ಷ": 100_000, "लाख": 100_000,
    "thousand": 1_000, "k": 1_000, "ಸಾವಿರ": 1_000, "हज़ार": 1_000, "हजार": 1_000,
}
AMOUNT = re.compile(r"(?:₹|rs\.?|inr)?\s*(\d[\d,]*(?:\.\d+)?)\s*(" + "|".join(UNITS) + r")?(?![\w])", re.I)

# The words just before or after an amount tell us which field it is.
MONEY_HINTS = [
    ("annual_turnover_inr", ("turnover", "sales", "ವಹಿವಾಟು", "टर्नओवर", "बिक्री")),
    ("family_annual_income_inr", ("family income", "income", "ಆದಾಯ", "आय")),
    ("loan_amount_needed_inr", ("loan", "need", "working capital", "borrow", "ಸಾಲ", "ಬೇಕು", "ऋण", "लोन", "चाहिए")),
    ("project_cost_inr", ("cost", "costing", "project", "invest", "ವೆಚ್ಚ", "लागत")),
]

TRADES = {
    "tailor": ("tailor", "tailoring", "stitch", "ದರ್ಜಿ", "ಟೈಲರ್", "ಹೊಲಿಗೆ", "दर्ज़ी", "दर्जी", "सिलाई"),
    "carpenter": ("carpenter", "ಬಡಗಿ", "बढ़ई"),
    "potter": ("potter", "pottery", "ಕುಂಬಾರ", "कुम्हार"),
    "blacksmith": ("blacksmith", "ಕಮ್ಮಾರ", "लोहार"),
    "goldsmith": ("goldsmith", "ಅಕ್ಕಸಾಲಿಗ", "सुनार"),
    "barber": ("barber", "salon", "ಕ್ಷೌರಿಕ", "नाई"),
    "cobbler": ("cobbler", "ಚಮ್ಮಾರ", "मोची"),
    "mason": ("mason", "ಗಾರೆ", "राजमिस्त्री"),
    "washerman": ("washerman", "laundry", "dhobi", "ಅಗಸ", "धोबी"),
    "garland_maker": ("garland", "ಹೂಮಾಲೆ", "माला"),
}

PLACES = {  # keyword -> (district, area_type or None)
    "mandya": ("Mandya", None), "ಮಂಡ್ಯ": ("Mandya", None), "मंड्या": ("Mandya", None),
    "jayanagar": ("Bengaluru Urban", "urban"), "kr market": ("Bengaluru Urban", "urban"),
    "k r market": ("Bengaluru Urban", "urban"), "bengaluru": ("Bengaluru Urban", "urban"),
    "bangalore": ("Bengaluru Urban", "urban"), "ಬೆಂಗಳೂರು": ("Bengaluru Urban", "urban"),
    "बेंगलुरु": ("Bengaluru Urban", "urban"), "mysuru": ("Mysuru", None), "mysore": ("Mysuru", None),
    "karnataka": (None, None), "ಕರ್ನಾಟಕ": (None, None), "कर्नाटक": (None, None),
}


def has(text: str, *words) -> bool:
    return any(w in text for w in words)


def find_amounts(text: str) -> list:
    """[(rupees, text around the number)] for every amount that has a unit or is 1000+."""
    out = []
    for m in AMOUNT.finditer(text):
        number, unit = float(m.group(1).replace(",", "")), (m.group(2) or "").lower()
        rupees = int(round(number * UNITS[unit])) if unit else int(number)
        if not unit and rupees < 1000:
            continue                     # a bare small number is an age or a count, not money
        out.append((rupees, text[max(0, m.start() - 40):m.start()], text[m.end():m.end() + 25]))
    return out


def extract(text: str) -> dict:
    t = " " + text.lower().strip() + " "
    p = {}

    for key, (district, area) in PLACES.items():
        if key in t:
            p["state"] = "KA"
            if district:
                p["district"] = district
            if area:
                p["area_type"] = area
            break
    if has(t, "village", "rural", "ಹಳ್ಳಿ", "ಗ್ರಾಮ", "गाँव", "गांव", "ग्रामीण"):
        p["area_type"] = "rural"
    elif has(t, " city", "urban", " town", "ನಗರ", "शहर"):
        p["area_type"] = "urban"

    for trade, words in TRADES.items():
        if has(t, *words):
            p["trade"], p["self_employed"] = trade, True
            break

    if has(t, "street vendor", "vendor", "hawker", "cart", "footpath", "ಬೀದಿ", "रेहड़ी", "ठेला", "फेरी"):
        p["business_activity"] = "street_vending"
        p.setdefault("trade", "none")
        p["self_employed"] = True
    elif has(t, "kirana", "shop", "store", "retail", "trader", "trading", "ಅಂಗಡಿ", "दुकान", "किराना"):
        p["business_activity"] = "trading"
        p.setdefault("trade", "none")
    elif has(t, "manufactur", "garment", "factory", " unit", "making", "ಘಟಕ", "ಗಾರ್ಮೆಂಟ್", "ತಯಾರಿಕೆ", "कारखाना", "इकाई"):
        p["business_activity"] = "manufacturing"
    elif has(t, "service", "repair", "salon", "ಸೇವೆ", "सेवा") or "trade" in p:
        p["business_activity"] = "service"

    if has(t, "want to start", "start a", "planning", "plan to", "new unit", "new business", "set up",
           "ಶುರು", "ಆರಂಭ", "ಹೊಸ", "शुरू", "नया", "नई"):
        p["is_new_project"] = True
    m = re.search(r"(\d{1,2})\s*(?:years?|yrs?)\s*(?:old\s+(?:shop|business|store)|in business|running)|(?:for|since)\s+(\d{1,2})\s*(?:years?|yrs?)", t)
    if m:
        p["years_operating"] = int(m.group(1) or m.group(2))
        p.setdefault("is_new_project", False)
    elif has(t, "i run", "i own", "i sell", "i have a", "existing", "ನಡೆಸುತ್ತಿದ್ದೇನೆ", "चलाता", "चलाती"):
        p.setdefault("is_new_project", False)

    m = re.search(r"(?:i am|i'm|aged?|age is)\s+(\d{2})\b(?!\s*(?:lakh|years? in))|(\d{2})\s*(?:years?|yrs?)[\s-]*old\b(?!\s+(?:shop|business|store))|(\d{2})\s*ವರ್ಷ|(\d{2})\s*साल की|(\d{2})\s*साल का", t)
    if m:
        p["owner_age"] = int(next(g for g in m.groups() if g))

    if has(t, "woman", "female", " she ", "lady", "housewife", "ಮಹಿಳೆ", "महिला"):
        p["owner_gender"] = "female"
    elif has(t, " man ", " male", "ಪುರುಷ", "पुरुष"):
        p["owner_gender"] = "male"

    for field, yes, no in [
        ("udyam_registered", ("udyam registered", "udyam-registered", "have udyam", "udyam and gst", "udyam- and gst"),
         ("not udyam", "no udyam", "without udyam")),
        ("gst_registered", ("gst registered", "gst-registered", "have gst", "with gst", "and gst"), ("no gst", "not gst", "without gst")),
        ("pan_available", ("have pan", "have a pan", "with pan"), ("no pan", "don't have pan", "do not have pan", "without pan", "ಪ್ಯಾನ್ ಇಲ್ಲ", "पैन नहीं")),
        ("has_vending_proof", ("vending certificate", "vending id", "letter of recommendation", "ವ್ಯಾಪಾರ ಪ್ರಮಾಣಪತ್ರ"), ("no vending certificate", "no certificate")),
        ("bank_account", ("bank account",), ("no bank account",)),
    ]:
        if has(t, *no):
            p[field] = False
        elif has(t, *yes):
            p[field] = True

    amounts = find_amounts(t)
    for rupees, before, after in amounts:
        field = next((f for f, hints in MONEY_HINTS if has(before[-30:], *hints)), None) \
            or next((f for f, hints in MONEY_HINTS if has(after, *hints)), None)
        if field is None and len(amounts) == 1:
            field = "project_cost_inr" if p.get("is_new_project") else "loan_amount_needed_inr"
        if field and field not in p:
            p[field] = rupees
    return p
