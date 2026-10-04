# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Small merchants in Karnataka: kirana owners, home manufacturers, artisans and street vendors. Many have low literacy and little experience with forms. They use budget Android phones, often on slow or patchy mobile data, and read Kannada, Hindi or English.

Their job: find out which government schemes their business may be eligible for, understand why or why not in plain words, and get ready to apply, without an agent or a long form.

Three personas are used in the demo (source: AGENTS.md 1.2):

- **Lakshmi**, 34, Mandya (rural). Home tailor planning a small garment unit costing ₹8 lakh. Not Udyam-registered. Prefers not to share caste.
- **Ravi**, 41, Jayanagar, Bengaluru. Kirana owner for 6 years, turnover ₹45 lakh, Udyam- and GST-registered, needs ₹4 lakh working capital.
- **Shabana**, 29, KR Market, Bengaluru. Fruit street vendor with a vending certificate, no PAN, needs ₹25,000. The low-literacy, voice-first case.

A second audience is the hackathon judges (Hacksprint PS21), who will ask how the engine decides.

## Product Purpose

LaabhMitra is a government benefits copilot for small Indian businesses. India has 5,000+ government schemes, but a merchant does not know which fit, why, which ones conflict, what is missing or how to apply.

The product builds a business profile in about 2 minutes, runs it through verified scheme rules, explains the results in Kannada, Hindi or English, picks the best combination of schemes that do not conflict, and prepares an application pack.

Success: a merchant leaves knowing which schemes to pursue, what one step would open more, and with documents ready for the official channel.

## Positioning

**AI explains. Rules decide. Government sources confirm.**

What a neighbouring product could not truthfully copy:

1. **Benefit Path Planner.** Picks the best set of schemes that can be combined (for example, a PMEGP or Mudra loan now can close the PM Vishwakarma route for 5 years).
2. **Honest money.** Grants, credit, fee savings and non-monetary benefits are separate buckets. Loans are never added to grants.
3. **Readiness tiers, not percentages.** Ready / Likely (needs info) / One step away / Not now / Watchlist, with "criteria met X of Y (Z unknown)".
4. **Why-not with fixes.** Every rejection names the rule and its source. Fixable gaps become steps that show what they unlock.
5. **Source and freshness.** Every scheme shows its official source, last-verified date and status.

## Operating Context

- Mobile-first web app, used on a phone, often one-handed, sometimes with a helper reading aloud.
- Profile is built by chat: tap answers, typed text, or voice (browser speech recognition in kn-IN, hi-IN, en-IN).
- Screens: onboarding and consent, scheme results by tier, scheme detail with Why? / Why not?, best path, application pack (checklist, draft, PDF, status tracker), what changed, project report for new units, and a hidden admin rule tester.
- Merchants apply themselves on official portals, banks or CSC centres. The app never submits anything.
- The demo must run with no internet (mock LLM, bundled fonts).

## Capabilities and Constraints

Capabilities (built):

- 12 schemes: 9 central, Udyam Assist, 1 Karnataka scheme, 1 watchlist item.
- Deterministic tri-state rules engine; estimators for subsidy and credit; conflict-aware path planner; fix plan; watch feed.
- Plain-language explanations in English, Kannada and Hindi, checked by a guard that rejects any number not in the facts.
- Loan affordability badge and a bank-style project report draft, both computed in code.

Constraints:

- Eligibility statuses and rupee amounts come only from the rules engine, never from an LLM.
- Never collect or store Aadhaar, PAN or bank account numbers, or passwords. Booleans only.
- Gender, social category, disability, widow status and income are optional, with "prefer not to say" and a reason for asking.
- Wording: "may be eligible" and "estimated". Never "guaranteed".
- Money is whole rupees, shown in Indian format (₹2,80,000).
- No government logos or emblems.
- Footer on every page: "Information only. Not affiliated with the Government of India. Final decisions are made by the implementing agency."
- Schemes with status "announced" appear only in the Watchlist.

Out of scope: submitting applications, Aadhaar/DigiLocker integration, live scraping of government portals, lending, referrals, payments, legal advice.

## Brand Commitments

- Name: **LaabhMitra** (working name). Kannada: ಲಾಭಮಿತ್ರ. Hindi: लाभमित्र.
- Voice: plain words, short sentences, honest about uncertainty. Says what is missing and what to do next.
- No logo or other brand asset exists yet.

## Evidence on Hand

- Scheme rules with sources and last-verified dates: `data/schemes.seed.json` (facts checked 4 Oct 2026).
- Demo personas: `data/personas.json`. Expected engine results: `data/expected.json`.
- Full spec: `AGENTS.md`.
- Kannada and Hindi text has not been reviewed by a native speaker.
- There are no testimonials, user research findings, usage numbers or pilot results. Future work must not invent them.

## Product Principles

1. **Rules decide, AI explains.** Nothing a model writes can change a status or an amount.
2. **Honest money.** Never make the opportunity look bigger than the rules support. Subsidies and loans stay apart.
3. **Unknown is not no.** Missing information is shown as unknown and turned into a question, not a rejection.
4. **Every "no" comes with a reason and, where possible, a next step.**
5. **Ask less.** Only ask what changes a result, and say why when the question is sensitive.

## Accessibility & Inclusion

- Low literacy: icons with every status, plain words, voice input, and a listen button on explanations.
- Three languages: Kannada, Hindi and English, switchable at any time.
- Budget phones: big tap targets (44px minimum), mobile-first layout, small page weight, works offline in demo mode.
- No required standard (such as a WCAG level) has been set.
