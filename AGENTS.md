# LaabhMitra: agent spec

Government Benefits Copilot for Small Businesses · Hacksprint PS21 · facts checked 4 Oct 2026.
Bootstrapped from `LaabhMitra_Cursor_Build_Spec.pdf` (Sections 1, 2, 3 and 5).

Product disclaimer: information only, not affiliated with the Government of India; estimates are not guarantees.

## How to work

- Work one milestone at a time (Section 3). Start by listing the files you will create or change, then implement, then run the tests and show the commands.
- Never edit `data/*.json` or the `.cursor/rules` files unless the user explicitly asks.
- Eligibility statuses and rupee amounts come only from the deterministic engine. The LLM only extracts, explains and drafts.
- The app must run end to end with `LLM_PROVIDER=mock` and no internet.
- Prefer simple, readable code: the student team must be able to explain it to judges.

---

# 1. Product context

**LaabhMitra** (working name) is a government benefits copilot for small Indian businesses (kirana owners, home manufacturers, artisans, street vendors), built for the Hacksprint PS21 problem statement (FinTech and Smart Commerce). India has 5,000+ government schemes (myScheme lists 5,056+ as of 28 Sep 2026), but a merchant does not know which fit, why, which ones conflict, what is missing or how to apply. The product: build a business profile in about 2 minutes, run it through verified scheme rules, explain results in Kannada/Hindi/English, choose the best non-conflicting combination of schemes, and prepare an application pack. **AI explains. Rules decide. Government sources confirm.**

## 1.1 What makes it different (must be visible in the product)

1. **Benefit Path Planner:** picks the best combination of schemes that do not conflict (e.g., a PMEGP or Mudra loan now can close the PM Vishwakarma route for 5 years).
2. **Honest money:** grants, credit, fee savings and non-monetary benefits are separate buckets; loans are never added to grants.
3. **Readiness tiers, not fake percentages:** Ready / Likely (needs info) / One step away / Not now / Watchlist, with 'criteria met X of Y (Z unknown)'.
4. **Why-not with fixes:** every rejection names the rule and source; fixable gaps become steps that show what they unlock.
5. **Source + freshness:** every scheme shows its official source, last-verified date and status (active / verify / announced).

## 1.2 Personas used in the demo

| Persona | Profile | What the demo proves |
|---|---|---|
| **Lakshmi**, 34, Mandya (rural, Karnataka) | Home tailor planning a small garment unit; project cost ₹8 lakh; not Udyam-registered; family income ₹1.4 lakh; prefers not to share caste. | Big subsidy found (PMEGP), conflict warning (PM Vishwakarma), 'why not' (Stand-Up India), unlock steps (Udyam), Kannada explanation. |
| **Ravi**, 41, Jayanagar, Bengaluru (urban) | Kirana owner, 6 years old, turnover ₹45 lakh, Udyam- and GST-registered, needs ₹4 lakh working capital. | Honesty: no grants match; three credit options (Mudra Kishore, CGTMSE via bank, ME-Card with a 'verify' badge). |
| **Shabana**, 29, KR Market, Bengaluru | Fruit street vendor with a vending certificate; no PAN; needs ₹25,000. | PM SVANidhi + Udyogini; Udyam Assist route; low-literacy voice flow. |

## 1.3 Feature list: what, why, how

Priority: **MUST** = in the demo, **SHOULD** = build if time allows, **STRETCH** = mention as roadmap or build only if ahead.

| # | Feature | Priority | Why (pain it removes) |
|---|---|---|---|
| F1 | 2-minute Merchant Profile (voice/text/chips) | MUST | Government forms ask 30+ questions; merchants quit. We ask 8-12 and infer the rest. |
| F2 | Rules-based eligibility engine (tri-state) | MUST | LLMs hallucinate eligibility; rules are auditable and testable. |
| F3 | Top opportunities with readiness tiers | MUST | 200 results = no decision. Show the top 5 that matter. |
| F4 | 'Why I qualify' plain-language explainer | MUST | Government language is the barrier. Translation layer in Kannada/Hindi/English. |
| F5 | 'Why not' + gap-closing plan | MUST | A silent rejection kills trust; a fixable gap becomes an action. |
| F6 | ₹ Opportunity Map (honest buckets) | MUST | Judges and users understand money; honesty builds trust. |
| F7 | Benefit Path Planner (conflicts) | MUST | Schemes interact; the wrong order can cost a merchant a scheme. |
| F8 | Application Pack (checklist + draft PDF) | MUST | 'I know I'm eligible but can't apply' is the last-mile drop-off. |
| F9 | Source and freshness badges | MUST | Prevents stale or announced-only schemes from being shown as available. |
| F10 | Proactive Opportunity Watch | SHOULD | Turns a search engine into an ongoing copilot. |
| F11 | Kannada/Hindi voice input + TTS | SHOULD | Low literacy and typing friction. |
| F12 | Outcome tracker (applied / sanctioned / received) | SHOULD | Measurable value: ₹ actually received. |
| F13 | Admin scheme editor + rule tester | SHOULD | Answers 'how do you scale beyond 12 schemes?' live. |
| F14 | Anti-fraud and 'free official channel' badges | SHOULD | Fake paid sites and agents exploit merchants. |
| F15 | Assisted mode for CSC / bank agents | STRETCH | Reaches non-smartphone users; the B2B2C revenue model. |
| F16 | Udyam certificate OCR to auto-fill profile | STRETCH | Zero-typing onboarding. |
| F17 | WhatsApp / SMS nudges | STRETCH | Re-engagement where merchants already are. |

### Feature details: how each one works

#### F1. 2-minute Merchant Profile

- **What:** a chat that asks only what eligibility needs: state/district, rural or urban, activity (manufacturing / service / trading / street vending), trade, new or existing unit, project cost or loan need, turnover and investment, Udyam/GST/PAN/bank, owner age and gender, plus OPTIONAL social category, family income, and existing government loans.
- **Why:** merchants drop off long forms. Asking 'why we need this' next to sensitive questions increases completion and respects privacy.
- **How:** (1) Free text or voice goes to an LLM tool call `extract_profile`, which returns JSON with only the allowed fields. (2) A Pydantic validator rejects unknown values. (3) Missing high-value fields trigger the NEXT best question. Choose the field that changes the most scheme statuses from UNKNOWN to TRUE/FALSE, a simple information-gain heuristic. (4) Chips for quick answers. (5) The profile is saved with consent and timestamp.
- **Demo:** Lakshmi says in Kannada or English: 'I'm a tailor in Mandya village, want to start a small garment unit costing 8 lakh'. The profile cards fill in live.

#### F2. Rules-based Eligibility Engine (the core IP)

- **What:** each scheme is a JSON object with criteria (field, operator, value, hard/soft, optional 'when' condition, fix action, source reference).
- **Why:** deterministic, explainable, unit-testable, and safe. The LLM never decides eligibility.
- **How:** tri-state logic. Each criterion returns TRUE / FALSE / UNKNOWN (field missing, or a value the sources disagree on) / N/A (its 'when' condition is false). Derived fields: enterprise_size (from the 1 Apr 2025 MSME limits), pmegp_special_category, female_or_scst, similar_loan_last_5y, udyogini_income_ok.
- **Status rules:** any hard FALSE that cannot be fixed means NOT_ELIGIBLE; one or two FALSE that can be fixed means NEAR_MISS; no FALSE but some UNKNOWN means LIKELY; everything TRUE means ELIGIBLE. A scheme with status 'announced' goes to the WATCHLIST. A scheme with status 'verify' gets a 'Check current status' badge.

#### F3. Top opportunities with readiness tiers

- **What:** five cards sorted by tier, then by grant value, then credit value. Each card shows the tier, 'criteria met X of Y (Z unknown)', the benefit bucket and the official source.
- **Why not a %:** a percentage implies a probability we cannot measure. If a judge insists, show 'fit' = met/total and 'confidence' = known/total, and say both are coverage measures, not approval odds.

#### F4. 'Why I qualify' explainer

- **How:** the LLM receives ONLY the scheme JSON, the per-criterion results and the user's language. It must write 3-5 short sentences, mention each criterion, and end with the source name. Output is checked: every number in the text must appear in the input JSON; otherwise the app falls back to a template explanation.
- **Example:** 'You qualify because you are 34 (18+ needed), this is a new unit, garment making counts as manufacturing, and ₹8 lakh is within the ₹50 lakh limit. As a woman in a rural area, the subsidy rate is 35%. Source: PMEGP guidelines.'

#### F5. 'Why not' + gap-closing plan

- **What:** for every FALSE criterion, show the plain reason and the source ('Stand-Up India needs a loan of at least ₹10 lakh; you need ₹7.2 lakh').
- **Fix actions:** fixable criteria (Udyam registration, PAN) become steps. Each step shows how many schemes it unlocks ('Register on Udyam: unlocks CGTMSE, ZED, ME-Card'). Rank steps by ₹ unlocked.

#### F6. ₹ Opportunity Map (honest)

- **Four buckets:** Grants and subsidies (non-repayable), Credit access (repayable loans or guarantees), Fee savings (e.g., ZED subsidy), Non-monetary (registration, certification). Never add loans to grants.
- **Estimators:** PMEGP = rate x min(project cost, cap): general 15% urban / 25% rural; special 25% / 35%. Caps: ₹50 lakh manufacturing, ₹20 lakh service/business. Udyogini = 30% of loan up to ₹90,000 (50% for SC/ST women). PM Vishwakarma toolkit ₹15,000. Credit amounts = loan need limited by the scheme cap.
- **If a sensitive field is 'prefer not to say':** show a range, e.g., 'Udyogini subsidy ₹90,000 (up to ₹1.5 lakh if SC/ST)'.
- **Label:** 'Estimated maximum. Final amount is decided by the implementing agency.'

#### F7. Benefit Path Planner (the 'wow' feature)

- **What:** picks the best set of schemes that can be combined, plus the order to apply.
- **How:** conflicts are data. 'anchor_excludes' example: PM Vishwakarma requires no PMEGP/Mudra/SVANidhi loan in the last 5 years. 'mutually_exclusive' example: two capital subsidies on the same project. Enumerate all subsets of candidate schemes (at most 12, so at most 4,096 subsets: instant), drop subsets that contain a conflict, and rank by maximum grant ₹, then credit ₹.
- **Show the top 2 paths with trade-offs.** Lakshmi, Path A: PMEGP (₹2.8 lakh subsidy, bank finances about 95%). Path B: PM Vishwakarma (₹15,000 toolkit + ₹3 lakh at 5%) + Udyogini (₹90,000 subsidy, up to ₹1.5 lakh if SC/ST).
- **Order hints:** 'Do free Udyam registration first; it unlocks 3 options.'

#### F8. Application Pack

- **Checklist:** documents you have vs still need (from the profile), with notes like 'needed only if you claim special category'.
- **Pre-filled draft:** the LLM writes a 1-page project summary or cover note from profile fields, watermarked 'DRAFT: review before use'. Rendered to PDF.
- **Official link + steps + status tracker:** Not started / Docs ready / Applied / Sanctioned / Received.
- **Never:** auto-submit, store Aadhaar numbers, or log in on the user's behalf.

#### F9. Source and freshness badges

- Each scheme has sources[] (title, URL, publisher), last_verified and status. Badges: 'Verified 4 Oct 2026', 'Check current status', 'Announced, not yet live'. An item older than 90 days turns amber automatically.

#### F10. Proactive Opportunity Watch

- **Triggers:** (a) profile change, e.g., Udyam registered, turnover crosses a limit, or a project moves from idea to new unit; (b) a scheme version changes (rules diff); (c) a watchlisted scheme becomes active; (d) the date passes a scheme's validity.
- **How:** re-run the engine, diff the old and new statuses, store notifications ('You now qualify for 2 more options'). Use an in-app feed for the demo; WhatsApp/SMS is a stretch goal.

#### F11. Voice and language

- Fastest MVP: the browser Web Speech API (free, no key; quality varies by browser and language). Better: Sarvam AI speech-to-text (pricing from the Sarvam docs; free starter credit for new accounts at the time of checking) or Bhashini (free APIs intended for proof-of-concept use).
- UI strings in JSON for en, kn and hi. Explanations are generated in the chosen language from structured facts.

#### F12-F17 in short

- **Outcome tracker:** the user marks applied, sanctioned or received with ₹. This powers 'measurable value' after a pilot.
- **Admin editor + rule tester:** paste a scheme JSON, run the 3 personas, see the statuses. Proves you can add schemes quickly.
- **Anti-fraud badges:** 'Udyam registration is free on the official portal' plus warnings about look-alike paid sites.
- **Assisted mode:** an agent profile with an explicit consent screen for each merchant.
- **Udyam certificate OCR:** extract Udyam number, enterprise type and activity from an uploaded PDF or image.
- **Nudges:** opt-in only, with frequency caps.

## 1.4 Scope

| In scope (MVP) | Stretch | Out of scope (say so clearly) |
|---|---|---|
| 12 schemes: 9 central + Udyam Assist + 1 Karnataka scheme + 1 watchlist; 3 personas; tri-state engine; tiers; explanations; why-not + fixes; Opportunity Map; Path Planner; Application Pack PDF; source/freshness badges; English + Kannada (+Hindi) UI; mock-LLM mode. | Voice via Sarvam; Udyam OCR; Proactive Watch feed; admin rule tester; outcome tracker; assisted mode. | Submitting applications on government portals; Aadhaar/DigiLocker integration; live scraping of myScheme; all 5,000 schemes; lending, referrals or payments; legal advice. |

---

# 2. Technical specification

## 2.1 Product requirements (prototype)

- A web app (mobile-first) where a merchant builds a profile by chat (text first; voice optional) and sees scheme results with readiness tiers, explanations, why-not reasons, fixes, an honest ₹ Opportunity Map, a Benefit Path Planner and an Application Pack PDF.
- Eligibility is computed ONLY by a deterministic rules engine over JSON scheme definitions. The LLM is used for (a) profile extraction, (b) plain-language explanations, (c) application drafts. Every LLM feature has a MOCK mode that works without internet or keys.
- Three demo personas load with one click (Lakshmi, Ravi, Shabana). The expected results are fixed by tests (Section 5).
- Languages: English and Kannada required, Hindi optional. Mobile-first UI.
- Every scheme card shows: tier, 'criteria met X of Y (Z unknown)', benefit bucket(s), status badge, last verified date, official link, and a 'Why?' button.

## 2.2 Tech stack and repo layout

```
laabhmitra/
  AGENTS.md                      # spec for the Agent (bootstrapped from this PDF)
  .cursor/rules/*.mdc            # short scoped project rules (Section 4)
  data/
    schemes.seed.json            # 12 schemes + conflicts (bootstrapped from this PDF)
    personas.json                # 3 demo personas (bootstrapped from this PDF)
    expected.json                # expected engine results (Appendix C)
    reference_engine.py          # tested reference implementation (Appendix D)
  backend/                       # Python 3.11, FastAPI, Pydantic v2, SQLModel (SQLite)
    app/
      main.py                    # FastAPI app, CORS, routers
      models.py                  # Pydantic: Profile, Scheme, Criterion, EvalResult, ...
      engine/
        derive.py                # derived fields (enterprise_size, special category, ...)
        evaluate.py              # tri-state criterion + scheme evaluation
        estimate.py              # benefit estimators (grant / credit buckets)
        paths.py                 # conflict-aware path planner
        fixes.py                 # gap-closing plan, unlock counts
        watch.py                 # diff old vs new results -> notifications
      llm/
        provider.py              # interface + MockProvider + AnthropicProvider/GeminiProvider
        prompts.py               # extract_profile, explain, why_not, draft_pack
        guard.py                 # JSON schema validation + numbers check
      pdf/pack.py                # ReportLab application pack
      routers/ profiles.py, schemes.py, evaluate.py, explain.py, pack.py, admin.py
      i18n/ en.json kn.json hi.json
    tests/ test_engine.py test_personas.py test_paths.py test_guard.py
  frontend/                      # React + Vite + TypeScript + Tailwind
    src/ pages/ (Onboard, Results, SchemeDetail, Path, Pack, Admin)
         components/ (ProfileChat, SchemeCard, TierBadge, OpportunityMap, PathView, SourceBadge)
         lib/api.ts  i18n/
  Makefile                       # make dev | make test | make seed
```

Environment variables: `LLM_PROVIDER` = mock | anthropic | gemini | openai | sarvam (default **mock**); `LLM_API_KEY`; `DEMO_MODE=true` (preloads personas).

## 2.3 Data model

### Merchant profile (all fields optional except where noted)

| Field | Type / allowed values | Notes |
|---|---|---|
| state, district | string (state code e.g. 'KA') | Required: state |
| area_type | urban \| rural | |
| business_activity | manufacturing \| service \| trading \| street_vending | Required |
| trade | one of 18 PM Vishwakarma trades \| 'none' | 'none' if not an artisan |
| self_employed | bool | |
| is_new_project | bool | true = starting a new unit |
| years_operating | int | |
| annual_turnover_inr, investment_plant_machinery_inr | int (rupees) | Ranges allowed in the UI; store the midpoint + flag |
| employees | int | |
| ownership_type | proprietorship \| partnership \| llp \| shg \| company \| other_noncorporate | |
| udyam_registered, gst_registered, pan_available, bank_account | bool | Never store PAN/Aadhaar NUMBERS |
| owner_age | int | |
| owner_gender | female \| male \| transgender \| prefer_not | Optional; explain why |
| social_category | general \| sc \| st \| obc \| minority \| prefer_not | Optional; explain why |
| is_ex_serviceman, is_differently_abled, is_widow | bool | Optional |
| education_8th_pass | bool | Asked only if PMEGP thresholds matter |
| family_annual_income_inr | int | Optional |
| project_cost_inr, loan_amount_needed_inr | int | |
| prior_govt_subsidy | bool | Subsidy already availed for this unit |
| existing_govt_loans | list of {scheme, year, repaid} | scheme in pmegp \| mudra \| pm_svanidhi \| other |
| previous_mudra_tarun_repaid, govt_employee_in_family, has_vending_proof | bool | |
| consent | {given: bool, timestamp, purposes[]} | Required before saving |

### Derived fields (computed in derive.py; never asked)

- **enterprise_size:** micro if investment up to ₹2.5 crore AND turnover up to ₹10 crore; small if up to ₹25 crore AND ₹100 crore; medium if up to ₹125 crore AND ₹500 crore; else large; None if either value is missing.
- **pmegp_special:** True if female, SC/ST/OBC/minority, ex-serviceman, differently-abled or transgender; None if gender or category is prefer_not/missing and nothing else is true; else False.
- **female_or_scst:** True if female or SC/ST; None if unknown; else False.
- **similar_loan_last_5y:** False if no PMEGP/Mudra/SVANidhi loan in the last 5 years; None if all such loans are repaid (an exception may apply); True otherwise.
- **udyogini_income_ok:** True if widow/differently-abled; else income below ₹2 lakh for SC/ST, below ₹1.5 lakh for general/OBC/minority; if category unknown: True below ₹1.5 lakh, False at ₹2 lakh or above, None in between.

### Scheme definition (JSON)

```jsonc
{
  "id": "pmegp", "short_name": "PMEGP", "name": "...", "level": "central|state", "state": null|"KA",
  "ministry": "...", "kind": "subsidy|credit|credit_guarantee|certification|registration|composite",
  "status": "active|verify|announced", "status_note": "...", "summary_plain": "...",
  "criteria": [
    {"id": "age", "label": "Owner is 18 or older", "field": "owner_age", "op": "gte", "value": 18,
     "hard": true, "source_ref": "s1",
     "when": {"field": "...", "op": "...", "value": ...} | {"all": [cond, cond]},   // optional
     "unknown_values": ["trading"],                                                // optional
     "fix": {"action_id": "register_udyam", "label": "..."},                       // optional
     "note": "..."}                                                                // optional
  ],
  "benefits": [{"type": "grant|credit|credit_guarantee|fee_subsidy|non_monetary", "label": "...",
                "amount_inr": 15000, "estimator": "pmegp_subsidy|udyogini_subsidy|mudra_tier"}],
  "rates": {...}, "documents": ["..."],
  "application": {"channel": "...", "url": "...", "steps": ["..."]},
  "sources": [{"id": "s1", "title": "...", "url": "...", "publisher": "..."}],
  "last_verified": "2026-10-04"
}
```

Operators: `eq, neq, in, not_in, gt, gte, lt, lte, between [lo, hi], is_true, is_false`

Conflicts (top-level array): `{"id", "schemes": [...], "type": "anchor_excludes|mutually_exclusive", "anchor"?, "message"}`

## 2.4 Engine specification

1. **Criterion evaluation:** if 'when' exists, evaluate it: FALSE gives N/A (skip), UNKNOWN gives UNKNOWN. If the field is missing (None), the result is UNKNOWN. If the value is in unknown_values, the result is UNKNOWN. Otherwise apply the operator and return TRUE or FALSE.
2. **Scheme status** (check in this order): status 'announced' gives WATCHLIST. Kind 'registration' and the user is already registered gives NOT_APPLICABLE. If any hard FALSE exists: all FALSE criteria have a fix and there are at most 2 of them gives NEAR_MISS, else NOT_ELIGIBLE. Else any hard UNKNOWN gives LIKELY. Else ELIGIBLE.
3. **Counts:** met = hard TRUE; total = hard criteria that are not N/A; unknown = hard UNKNOWN.
4. **Estimators** return {grant_min, grant_max, credit, fee_saving_note}. PMEGP: base = min(project_cost, cap); rate from (special?, area). If special is None, the range is general to special. Bank finance = base x (1 - own contribution). Udyogini: loan = min(need, 3 lakh); general 30% capped at ₹90,000; SC/ST 50% capped at ₹1.5 lakh; range if category unknown. PM Vishwakarma: grant ₹15,000, credit ₹3 lakh. Mudra: credit = min(need, ₹20 lakh) with the tier name. SVANidhi: ₹15,000 first tranche. ME-Card: ₹5 lakh. CGTMSE: credit = loan need (guarantee).
5. **Path planner:** candidates = schemes with status ELIGIBLE, LIKELY or NEAR_MISS, kind not registration, and grant_max > 0. Build a set of forbidden pairs from the conflicts (anchor_excludes: anchor vs each other scheme; mutually_exclusive: every pair). Enumerate all subsets, drop subsets that contain a forbidden pair, keep only maximal subsets, sort by (grant_max desc, size desc), and return the top 3 with the conflict messages that separate them. Credit options are listed separately; never added to grants.
6. **Fix plan:** for each fix action_id, count the schemes whose ONLY failing criteria use that fix and sum their grant_max and credit. Sort by grant ₹, then count.
7. **Watch diff:** compare previous vs new status per scheme. Emit a notification when a status improves, a 'verify' badge appears, or a watchlisted scheme becomes active.
8. **Staleness:** if today minus last_verified is more than 90 days, show the amber 'Re-verify' badge.
9. **Display rules:** show Udyam Assist only when the user has no PAN (otherwise recommend full Udyam Registration). Show a WATCHLIST scheme only if it has no hard FALSE criteria. Hide NOT_APPLICABLE items.

## 2.5 LLM layer (with guardrails)

| Task | Input | Output + guard |
|---|---|---|
| extract_profile | Free text or transcript + allowed field list + enums | JSON with only allowed keys; Pydantic validation; unknown keys dropped; ask a follow-up for low-confidence fields. Mock: regex/keyword extractor for the 3 persona sentences. |
| explain_eligibility | Scheme JSON + per-criterion results + language | 3-5 sentences. Every number in the output must appear in the input (regex check); otherwise use the template. Must end with the source title. |
| explain_why_not | Failing/unknown criteria + fixes | Short reason per criterion + a fix if one exists; same numbers check. |
| draft_pack | Profile + scheme + documents | 1-page project summary/cover note marked DRAFT; no invented facts; placeholders like [fill in] for missing data. |

```
SYSTEM PROMPT (explain_eligibility)
You explain government scheme eligibility to a small business owner in {language}.
Use ONLY the facts in the JSON below. Do not add schemes, amounts, dates or conditions.
Say "may be eligible", never "will get". Keep sentences short (max 15 words).
Mention each criterion result once. End with: "Source: {source_title}".
If a criterion is UNKNOWN, say what information is missing.
FACTS: {scheme_json} RESULTS: {criteria_results} PROFILE: {relevant_profile_fields}
```

## 2.6 API endpoints

| Method + path | Purpose |
|---|---|
| GET /api/schemes | List schemes (id, name, status, last_verified) |
| GET /api/personas | Demo personas |
| POST /api/profiles | Create/update a profile (requires consent); returns profile_id |
| POST /api/extract | Text or transcript to a partial profile (LLM or mock) |
| POST /api/evaluate | {profile or profile_id} to per-scheme results + estimates + tiers |
| GET /api/opportunity-map/{profile_id} | Buckets (grants, credit, fee savings, non-monetary) + best paths + fix plan |
| POST /api/explain | {profile_id, scheme_id, lang, kind: why\|why_not} to text + source |
| POST /api/pack | {profile_id, scheme_id, lang} to PDF (application pack) |
| GET /api/watch/{profile_id} | Notifications feed (diffs) |
| POST /api/admin/test-scheme | Paste a scheme JSON; run the personas; return statuses (rule tester) |

## 2.7 Screens

1. **Onboard:** language picker (English / Kannada / Hindi), consent screen, chat with chips + mic button; a live 'Your business' card on the side; 'Load demo persona' buttons.
2. **Results:** headline: 'Up to ₹X in subsidies (estimated) + ₹Y collateral-free credit options'. Tabs: Ready / Likely / One step away / Not now / Watchlist. Scheme cards.
3. **Scheme detail:** criteria checklist with ✓ / ✗ / ? icons, 'Why?' and 'Why not?' buttons, source badge, documents, official link, 'Prepare application'.
4. **Best path:** Path A vs Path B side by side with conflict warnings and order of steps; unlock steps ('Register on Udyam: unlocks 3').
5. **Application Pack:** checklist (have / need), draft preview, Download PDF, status tracker.
6. **Watch:** notification feed; 'What changed' (e.g., after toggling Udyam registered = yes).
7. **Admin (hidden route /admin):** JSON editor + 'Run persona tests' table.

UI rules: big tap targets, plain words, icons with every status, ₹ in Indian format (₹2,80,000), a disclaimer in the footer: 'Information only. Not affiliated with the Government of India. Final decisions are made by the implementing agency.'

## 2.8 Hard constraints for the Cursor Agent

- Never let an LLM output change eligibility status or ₹ amounts.
- Never call or scrape government portals at runtime; data comes only from /data.
- Never collect or store Aadhaar/PAN numbers, bank account numbers or passwords. Only booleans like pan_available.
- Sensitive fields (gender, social category, disability, widow status, income) are optional with 'prefer not to say' and an explanation of why they are asked.
- All money is stored as integer rupees; format with the Indian numbering system in the UI.
- Every scheme card must show its source and status badge; schemes with status 'announced' appear only in the Watchlist.
- Use the words 'may be eligible' and 'estimated'; never 'guaranteed'.
- The app must run end to end with LLM_PROVIDER=mock and no network.


## 2.9 Affordability check

For every scheme result that involves a loan, show whether the repayment fits the merchant's cash. This is a **warning badge only**: it never changes eligibility status, tiers, path planner results or `data/expected.json`.

- **Profile fields (optional):** `monthly_sales_inr`, `monthly_costs_inr` (all business costs incl. purchases, rent, wages), `existing_emis_inr` (monthly). The chat asks them last, each with a "why we ask" note. They are not asked for a new unit.
- **Assumptions** (`engine/affordability_config.py`; not official figures): `DEFAULT_ANNUAL_RATE = 0.12`, `DEFAULT_TENURE_MONTHS = 60`, `SCHEME_RATE_OVERRIDES = {"pm_vishwakarma": 0.05}` (the scheme's stated rate), `COMFORTABLE_MAX = 0.30`, `TIGHT_MAX = 0.40`, `NO_FIXED_EMI = {"me_card"}` (revolving credit).
- **Formula** (`engine/affordability.py`): `emi(P, annual_rate, n) = P*r*(1+r)^n / ((1+r)^n - 1)`, `r = annual_rate/12`; rounded to whole rupees for display only.
- **Principal:** the scheme's estimated credit from `estimate.py`. For PMEGP this is the bank-finance figure (note: "conservative: ignores how the bank adjusts the subsidy").
- **Bands:** `monthly_surplus = monthly_sales_inr - monthly_costs_inr - existing_emis_inr`; `ratio = EMI / monthly_surplus`. `<= 0.30` Comfortable; `<= 0.40` Tight; `> 0.40` or surplus `<= 0` "May strain your cash". Any input missing: "Unknown" with "Add monthly sales and costs to check affordability". `me_card`: "No fixed EMI; interest depends on usage".
- **New projects** (`is_new_project = true`): use the project report's year-1 DSCR (2.10) with the DSCR bands, `basis: "project_report"`. Without a report: "Unknown: needs a project report".
- **Result:** `{principal, annual_rate, tenure_months, emi, monthly_surplus, ratio, dscr, band, band_key, basis: "current_cash" | "project_report", message, assumptions_note}`.
- **API:** each scheme result from `POST /api/evaluate` carries `"affordability"` (null when the scheme has no loan). `POST /api/affordability {profile | profile_id, scheme_id, annual_rate?, tenure_months?}` recomputes with the merchant's own rate and tenure.
- **UI:** credit cards show an EMI badge (green Comfortable / amber Tight / red May strain / grey Unknown) and "Estimated EMI ₹X/month at Y% for Z months (assumed; your bank's rate may differ)". Scheme Detail has rate and tenure sliders. Never the word "guaranteed".
- **Tests:** `backend/tests/test_affordability.py`.

## 2.10 Project report

A bank-style project report draft for a new unit (PMEGP first). **All numbers are computed in code.** The LLM only writes short narrative sections and must pass `guard.py`. Every PDF page is watermarked "DRAFT: review before use".

- **Inputs:** optional `project` object in the profile, filled on the "Project report" page: `machinery_inr`, `building_or_civil_inr` (0 if rented), `working_capital_inr`, `monthly_sales_year1_inr`, `annual_sales_growth` (fraction), `raw_material_pct_of_sales` (fraction), `monthly_fixed_costs_inr`, `business_description`. Project cost = machinery + building + working capital. If it differs from `profile.project_cost_inr` the report returns `cost_mismatch` and the UI asks which is right.
- **Assumptions** (`engine/project_report_config.py`): loan rate and tenure reuse the affordability defaults; `MACHINERY_DEPRECIATION = 0.10` and `BUILDING_DEPRECIATION = 0.05` per year, straight-line; `YEARS = 3`; DSCR bands (banks set their own minimum): `< 1.0` "Cannot cover repayments", `1.0-1.5` "Thin", `>= 1.5` "Comfortable". Taxes are ignored: all profits are "before tax".
- **Means of finance** (`engine/project_report.py`): own contribution = project cost x the PMEGP own-contribution rate from the seed data (special 5% / general 10%; 10% if special category is unknown). Bank loan = project cost - own contribution. The PMEGP subsidy estimate (`grant_min` from `estimate.py`) is a separate line: "Margin-money subsidy (estimated; adjusted by the bank as per scheme rules)". How the bank adjusts the subsidy is not modelled, and the report says so.
- **Loan schedule:** monthly amortisation with the 2.9 EMI formula, summed per year into interest and principal.
- **Projection, year y = 1..3:** sales = monthly_sales_year1 x 12 x (1+growth)^(y-1); raw material = pct x sales; fixed = monthly_fixed x 12; depreciation; interest; profit before tax = sales - raw material - fixed - depreciation - interest; cash accrual = profit before tax + depreciation; DSCR = (cash accrual + interest) / (principal repaid + interest). Average DSCR over 3 years gives the band.
- **Link to 2.9:** for `is_new_project = true` with complete project details, affordability uses the year-1 DSCR (computed for that scheme's own loan amount and rate) with the DSCR bands, `basis: "project_report"`.
- **LLM task `draft_project_narrative`:** sections About the business, Market and customers, Why it is viable. Input = `business_description` + computed figures only. Mock mode returns templates. Each section is checked by `guard.py`; a section with a number not in the figures (or banned wording) is replaced by its template. ID-like numbers in the description are redacted first.
- **PDF** (`pdf/project_report.py`, ReportLab): cover with DRAFT watermark, project summary, cost of project, means of finance, 3-year projection, yearly loan repayment schedule, DSCR table, assumptions, narrative sections, `[fill in]` for missing data, and the disclaimer "Information only. Not affiliated with the Government of India."
- **API:** `POST /api/project-report {profile_id | profile, annual_rate?, tenure_months?}` returns the JSON report (or `{complete: false, missing: [...]}`); `GET /api/project-report/{profile_id}/pdf` returns the PDF.
- **Tests:** `backend/tests/test_project_report.py` (Lakshmi sample: EMI 16906; DSCR 2.07 / 2.43 / 2.82; average 2.44, "Comfortable").

---

# 3. Milestones (one per user request; start each from a fresh chat with @AGENTS.md)

### M0: Scaffold

Create the monorepo layout from 2.2: FastAPI backend, React + Vite + TypeScript + Tailwind frontend, a Makefile (dev, test) plus equivalent npm/python commands that work on Windows, a /api/health endpoint and a README with run steps. Keep data/ and .cursor/ unchanged. No features yet. List files first, create them, then give the exact run commands.

### M1: Engine + tests

Implement backend/app/models.py (Pydantic: Profile, Scheme, Criterion, Conflict, EvalResult) and backend/app/engine/derive.py, evaluate.py, estimate.py by porting data/reference_engine.py into the package (follow 2.3 and 2.4). Write backend/tests/test_personas.py that loads data/expected.json and asserts every status, met/total/unknown, grant_min, grant_max, credit and best_paths for all 3 personas x 12 schemes, plus unit tests for every operator, 'when', unknown_values, staleness and display rules. Run pytest until green. No LLM code. Never edit data/.

### M2: Paths, fixes, API

Implement engine/paths.py, fixes.py, watch.py and all API endpoints in 2.6 except the LLM ones. Tests: Lakshmi's two best paths, her fix plan (register_udyam unlocks CGTMSE, ZED, ME-Card) and the watch diff after setting udyam_registered=true. OpenAPI docs at /docs.

### M3: Frontend core

Onboard page (form with chips, chat style), Results page (tabs by readiness tier; scheme cards with tier badge, 'criteria met X of Y (Z unknown)', benefit buckets, status/freshness badge, official link) and Scheme Detail page, using the M2 API. 'Load demo persona' buttons for Lakshmi, Ravi, Shabana. Mobile-first, Indian rupee format, English only for now.

### M4: LLM layer (mock first)

backend/app/llm/provider.py with MockProvider (templates + keyword extractor for the 3 persona sentences) and one real provider chosen by LLM_PROVIDER. Implement extract_profile, explain_eligibility, explain_why_not with the 2.5 prompts, and guard.py (schema validation, numbers check, template fallback). Wire Why? / Why not? and the chat box. Guard tests. Must still work with LLM_PROVIDER=mock offline.

### M5: Opportunity Map, Path view, Pack

Opportunity Map (4 buckets, never add credit to grants, 'how calculated' panel), Best Path view (Path A vs B, conflict warnings, unlock steps) and Application Pack (have/need checklist, LLM draft marked DRAFT, ReportLab PDF download, status tracker in SQLite).

### M6: Watch + Admin

Watch feed (store previous results, show diffs after a profile edit) and hidden /admin rule tester (paste scheme JSON, validate, run the 3 personas, show statuses).

### M7: Language, voice, polish

i18n (en, kn, hi) for all UI strings; explanations in the chosen language. Mic button with the browser Web Speech API (kn-IN, hi-IN, en-IN) and text fallback; optional Sarvam speech-to-text behind an env flag. Consent screen, privacy note, disclaimer footer, offline demo mode. Loading, empty and error states; basic accessibility.

**Definition of done for every milestone:** all tests pass, the app starts with the documented command, no edits to data/ or .cursor/, and a short summary of what changed and how to try it.

---

# 5. Acceptance tests (summary of data/expected.json)

Produced by running data/reference_engine.py on the seed data. The engine you build must reproduce data/expected.json exactly. Format: STATUS (met/total, unknown?).

| Scheme | Lakshmi (Mandya, KA) | Ravi (Jayanagar, Bengaluru) | Shabana (KR Market, Bengaluru) |
|---|---|---|---|
| Udyam Registration | ELIGIBLE (2/2, 0?) | NOT_APPLICABLE (1/2, 0?) fails: not_yet | NEAR_MISS (1/2, 0?) fails: pan |
| Udyam Assist | ELIGIBLE (2/2, 0?) | NOT_APPLICABLE (0/2, 0?) fails: not_yet, no_gst | ELIGIBLE (2/2, 0?) |
| PMEGP | ELIGIBLE (5/5, 0?) grant ₹2,80,000 credit ₹7,60,000 | NOT_ELIGIBLE (2/6, 3?) fails: new | NOT_ELIGIBLE (2/4, 0?) fails: new, activity |
| PM Mudra (PMMY) | ELIGIBLE (3/3, 0?) credit ₹7,20,000 | ELIGIBLE (3/3, 0?) credit ₹4,00,000 | ELIGIBLE (3/3, 0?) credit ₹25,000 |
| CGTMSE | NEAR_MISS (2/3, 0?) fails: udyam credit ₹7,20,000 | ELIGIBLE (3/3, 0?) credit ₹4,00,000 | NEAR_MISS (2/3, 0?) fails: udyam credit ₹25,000 |
| PM Vishwakarma | ELIGIBLE (5/5, 0?) grant ₹15,000 credit ₹3,00,000 | NOT_ELIGIBLE (4/5, 0?) fails: trade | NOT_ELIGIBLE (4/5, 0?) fails: trade |
| PM SVANidhi | NOT_ELIGIBLE (0/2, 0?) fails: vendor, proof | NOT_ELIGIBLE (0/2, 0?) fails: vendor, proof | ELIGIBLE (2/2, 0?) credit ₹15,000 |
| Stand-Up India | NOT_ELIGIBLE (4/5, 0?) fails: min | NOT_ELIGIBLE (2/5, 0?) fails: who, greenfield, min | NOT_ELIGIBLE (3/5, 0?) fails: greenfield, min |
| ZED Certification | NEAR_MISS (2/3, 0?) fails: udyam | LIKELY (2/3, 1?) | NOT_ELIGIBLE (1/3, 0?) fails: udyam, activity |
| ME-Card | NEAR_MISS (1/2, 0?) fails: udyam credit ₹5,00,000 | ELIGIBLE (2/2, 0?) credit ₹5,00,000 | NEAR_MISS (1/2, 0?) fails: udyam credit ₹5,00,000 |
| Udyogini (Karnataka) | LIKELY (4/5, 1?) grant ₹90,000-₹1,50,000 credit ₹3,00,000 | NOT_ELIGIBLE (3/5, 0?) fails: woman, income | ELIGIBLE (5/5, 0?) grant ₹7,500-₹12,500 credit ₹25,000 |
| First-time Women/SC/ST Entrepreneurs Loan | WATCHLIST (2/2, 0?) | WATCHLIST (0/2, 0?) fails: who, first | WATCHLIST (1/2, 0?) fails: first |

- **Lakshmi best paths:** PMEGP (grant ₹2,80,000); PM Vishwakarma + Udyogini (grant ₹1,05,000 to ₹1,65,000).
- **Ravi:** no grant path; credit options Mudra (Kishore, ₹4,00,000), CGTMSE (via bank), ME-Card (₹5,00,000, verify badge).
- **Shabana:** grant path Udyogini (₹7,500 to ₹12,500); credit PM SVANidhi ₹15,000 first tranche, Mudra Shishu ₹25,000.
- **Guard:** an explanation containing a number not present in the facts must be replaced by the template.
