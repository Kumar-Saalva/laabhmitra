"""Template text built from engine facts. Used by the mock provider and as the fallback
whenever a real LLM answer fails the guard. Templates never add a fact of their own."""
from app import i18n
from app.engine.derive import DERIVED_INPUTS
from app.money import format_inr

SHOW_ESTIMATE = ("ELIGIBLE", "LIKELY", "NEAR_MISS")
ACTIVITY_WORDS = {"manufacturing": "manufacturing", "service": "service", "trading": "trading",
                  "street_vending": "street vending"}


def build_facts(profile: dict, scheme: dict, result: dict) -> dict:
    """The only things an LLM is allowed to see: scheme facts, criterion results, needed profile fields."""
    needed = set()
    for c in scheme["criteria"]:
        conds = [c] + (c["when"].get("all", [c["when"]]) if c.get("when") else [])
        for cond in conds:
            needed.update(DERIVED_INPUTS.get(cond["field"], [cond["field"]]))
    est = result["estimate"]
    return {
        "scheme": {k: scheme.get(k) for k in ("id", "short_name", "name", "status", "status_note",
                                              "summary_plain", "benefits", "rates")},
        "status": result["status"],
        "results": [{"id": c["id"], "label": c["label"], "result": c["result"], "note": c.get("note"),
                     "fix": (c.get("fix") or {}).get("label")}
                    for c in result["criteria"] if c["result"] != "N/A"],
        "estimate": {k: est.get(k) for k in ("grant_min", "grant_max", "credit", "tier_name")},
        "profile": {f: profile.get(f) for f in sorted(needed) if profile.get(f) not in (None, [])},
        "documents": scheme.get("documents", []),
        "source_title": scheme["sources"][0]["title"],
    }


def draft_facts(profile: dict, scheme: dict, result: dict) -> dict:
    """Facts for the cover note: the whole profile (never any ID number: the model has none)."""
    facts = build_facts(profile, scheme, result)
    facts["profile"] = {k: v for k, v in profile.items() if v not in (None, []) and k != "consent"}
    return facts


def _your_value(profile: dict, field: str):
    value = profile.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return format_inr(value) if field.endswith("_inr") else str(value)


def _estimate_lines(tx: dict, result: dict) -> list:
    if result["status"] not in SHOW_ESTIMATE:
        return []
    est, lines = result["estimate"], []
    if est["grant_max"] > 0:
        if est["grant_min"] != est["grant_max"]:
            lines.append(tx["grant_range"].format(lo=format_inr(est["grant_min"]), hi=format_inr(est["grant_max"])))
        else:
            lines.append(tx["grant"].format(amount=format_inr(est["grant_max"])))
    if est["credit"] > 0:
        lines.append(tx["credit"].format(amount=format_inr(est["credit"])))
    if lines:
        lines.append(tx["agency"])
    return lines


def explain(kind: str, profile: dict, scheme: dict, result: dict, lang: str) -> str:
    tx = i18n.texts(lang)
    lines = [tx["intro"][result["status"]].format(scheme=scheme["short_name"])]
    shown = [c for c in result["criteria"] if c["result"] != "N/A" and c["hard"]]
    if kind == "why_not":
        shown = [c for c in shown if c["result"] in ("FALSE", "UNKNOWN")]
        if not shown:
            lines.append(tx["nothing_blocking"])
    for c in shown:
        label = i18n.criterion_label(lang, scheme["id"], c)
        if c["result"] == "TRUE":
            lines.append(tx["met"].format(label=label))
        elif c["result"] == "UNKNOWN":
            lines.append(tx["need_info"].format(label=label))
        else:
            line = tx["not_met"].format(label=label)
            yours = _your_value(profile, c["field"])
            if yours:
                line += " " + tx["yours"].format(value=yours)
            if c.get("fix"):
                line += " " + tx["fix"].format(fix=i18n.fix_label(lang, c["fix"]))
            lines.append(line)
    if kind == "why":
        lines += _estimate_lines(tx, result)
    if scheme["status"] == "verify":
        lines.append(tx["check_status"])
    lines.append(tx["source"].format(title=scheme["sources"][0]["title"]))
    return "\n".join(lines)


def draft(profile: dict, scheme: dict, result: dict) -> str:
    """One-page cover note in English (the language of most application forms).
    Missing facts become [fill in]; nothing is invented."""
    def val(field, money=False):
        v = profile.get(field)
        if v is None:
            return "[fill in]"
        return format_inr(v) if money else str(v)

    activity = ACTIVITY_WORDS.get(profile.get("business_activity"), "[fill in]")
    trade = profile.get("trade")
    trade_text = f" ({trade.replace('_', ' ')})" if trade and trade != "none" else ""
    stage = {True: "I plan to start a new", False: "I run an existing"}.get(profile.get("is_new_project"), "I have a")
    place = ", ".join(x for x in (profile.get("district"), profile.get("state")) if x) or "[fill in]"
    area = f" ({profile['area_type']} area)" if profile.get("area_type") else ""
    channel = scheme["application"].get("channel") or "[fill in]"
    documents = "\n".join(f"  - {d}" for d in scheme.get("documents", [])) or "  - [fill in]"

    lines = [
        "DRAFT: review before use",
        "",
        f"To: {channel}",
        f"Subject: Application under {scheme['name']}",
        "",
        "Respected Sir/Madam,",
        "",
        f"{stage} {activity} business{trade_text} at {place}{area}. "
        f"I wish to apply under {scheme['short_name']} and request you to consider my application.",
        "",
        "About the business",
        f"  Owner name: [fill in]",
        f"  Business name and address: [fill in]",
        f"  Years in operation: {val('years_operating')}",
        f"  Annual turnover: {val('annual_turnover_inr', money=True)}",
        f"  Project cost: {val('project_cost_inr', money=True)}",
        f"  Loan amount needed: {val('loan_amount_needed_inr', money=True)}",
        f"  People employed: {val('employees')}",
        "",
        "Purpose of the funds: [fill in]",
        "",
        "Documents enclosed",
        documents,
        "",
        "I confirm that the information above is true to the best of my knowledge.",
        "",
        "Name: [fill in]        Signature: [fill in]        Date: [fill in]",
    ]
    return "\n".join(lines)


NARRATIVE_SECTIONS = ["about", "market", "viability"]
NARRATIVE_TITLES = {"about": "About the business", "market": "Market and customers", "viability": "Why it is viable"}


def narrative_facts(profile: dict, report: dict) -> dict:
    """What the LLM may see for the project narrative: the description and the computed figures."""
    description = (profile.get("project") or {}).get("business_description")
    return {
        "business_description": description,
        "business": {k: profile.get(k) for k in ("business_activity", "trade", "district", "state", "area_type")
                     if profile.get(k) not in (None, "none")},
        "figures": {k: report[k] for k in ("cost_of_project", "means_of_finance", "loan", "years",
                                           "average_dscr", "band")},
    }


def project_narrative(profile: dict, report: dict) -> dict:
    """Template narrative (mock mode and guard fallback). Every number comes from the report."""
    description = ((profile.get("project") or {}).get("business_description") or "").strip() or "[fill in]"
    activity = ACTIVITY_WORDS.get(profile.get("business_activity"), "[fill in]")
    place = ", ".join(x for x in (profile.get("district"), profile.get("state")) if x) or "[fill in]"
    cost, finance, loan = report["cost_of_project"], report["means_of_finance"], report["loan"]
    first, last = report["years"][0], report["years"][-1]
    return {
        "about": (
            f"{description} The unit is a {activity} business at {place}. "
            f"The total project cost is {format_inr(cost['total'])}: {format_inr(cost['machinery'])} for machinery, "
            f"{format_inr(cost['building_or_civil'])} for building or civil work and "
            f"{format_inr(cost['working_capital'])} for working capital. "
            f"The owner brings {format_inr(finance['own_contribution'])} and a bank loan of "
            f"{format_inr(finance['bank_loan'])} is requested."
        ),
        "market": (
            "Customers and where they are: [fill in]. How the unit will reach them: [fill in]. "
            f"Sales are projected at {format_inr(first['sales'])} in year {first['year']}, "
            f"rising to {format_inr(last['sales'])} in year {last['year']}."
        ),
        "viability": (
            f"Projected profit before tax is {format_inr(first['profit_before_tax'])} in year {first['year']} "
            f"and {format_inr(last['profit_before_tax'])} in year {last['year']}. "
            f"The estimated monthly instalment is {format_inr(loan['emi'])}. "
            f"The debt service coverage ratio is {first['dscr']} in year {first['year']} and "
            f"{report['average_dscr']} on average, which is in our '{report['band']}' band. "
            "These are estimates from the owner's own figures, before tax. Banks set their own minimum."
        ),
    }
