# LaabhMitra

Government benefits copilot for small Indian businesses (Hacksprint PS21).
A merchant describes their business in about two minutes; written rules decide which
schemes fit; the app explains why, shows what is missing, picks the best combination
that does not conflict, and prepares an application pack.

**AI explains. Rules decide. Government sources confirm.**

Information only. Not affiliated with the Government of India. Estimates are not guarantees.

## Run it (Windows, two terminals)

Needs Python 3.11+ and Node.js 20+.

Easiest on Windows: double-click **start.bat**. It opens the API, the web app and your browser.

One-time setup:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
npm --prefix frontend install
```

Terminal 1, the API (http://127.0.0.1:8000, docs at /docs):

```powershell
npm run api
```

Terminal 2, the web app (http://localhost:5173):

```powershell
npm run web
```

Tests:

```powershell
npm test                 # backend: engine, paths, guard, API (pytest)
npm run typecheck        # frontend: TypeScript
python data\reference_engine.py   # must print MATCHES expected.json
```

On macOS/Linux use `make setup`, `make api`, `make web`, `make test`.

## Try the demo

1. Open http://localhost:5173, pick a language, tick the consent box, press Start.
2. Press **Lakshmi** under "Try a demo business". You get: PMEGP subsidy up to ₹2,80,000,
   and a hint that Udyam registration opens 3 more options.
3. **Best path** shows Path A (PMEGP) against Path B (PM Vishwakarma + Udyogini) with the
   conflict warning.
4. Open **Stand-Up India** under "Not now" and press **Why not?** Switch the language to
   ಕನ್ನಡ to get the explanation in Kannada.
5. Open PMEGP, press **Prepare application**, download the PDF.
6. **What changed**: press "I registered on Udyam" and three schemes move to Ready.
7. **Ravi** shows the honest case: no subsidy, three credit options. **Shabana** shows
   PM SVANidhi, Udyogini and the Udyam Assist route.
8. Or type in the chat: `I'm a tailor in Mandya village, want to start a small garment unit costing 8 lakh`.
9. The rule tester is at http://localhost:5173/admin (hidden route).
10. **Affordability:** load **Ravi**, go to "My business" and answer the three monthly questions the
    chat asks last (type 375000 for sales, 340000 for costs, tap ₹0 for instalments). His Mudra card
    then shows "Repayment: Comfortable" with an estimated EMI of ₹8,898. Open the scheme to move the
    rate and tenure sliders.
11. **Project report:** load **Lakshmi**, open the **Project report** tab, enter machinery 500000,
    building 0, working capital 300000, monthly sales 120000, fixed costs 25000, raw material 50,
    growth 10, and press **Calculate report**. Download the PDF.

## How the engine decides (for judges)

Everything below lives in `backend/app/engine/` and is plain Python with tests.

1. `derive.py` adds facts we never ask for (enterprise size, special category, ...).
   A fact we cannot work out is `None`.
2. `evaluate.py` checks each criterion and returns `TRUE`, `FALSE`, `UNKNOWN` or `N/A`.
   Missing information is `UNKNOWN`, never a guess.
3. Scheme status, in this order: announced → Watchlist; already registered → hidden;
   failing rules that can all be fixed (at most 2) → One step away; any other failing
   rule → Not now; unknown rules → Likely; otherwise → Ready.
4. `estimate.py` works out rupee amounts with fixed formulas. Subsidies and credit are
   separate numbers and are never added.
5. `paths.py` tries every combination of subsidy schemes, drops the ones that contain a
   conflict, and keeps the best. `fixes.py` finds single steps that unlock schemes.
   `watch.py` compares old and new results.

6. `affordability.py` compares a loan's estimated monthly instalment with the cash the business
   has left each month. It is a warning badge only and never changes a status. `project_report.py`
   computes the bank-style report for a new unit (cost, finance, 3-year projection, DSCR).
   The assumed rates, tenures and bands are in the two `*_config.py` files, labelled as assumptions.

The LLM layer (`backend/app/llm/`) only reads a profile out of free text, rewords engine
results, and drafts a cover note. `guard.py` rejects any LLM text that contains a number
not present in the facts, or the words "guaranteed" / "will get", and falls back to a
template. The default provider is `mock`: templates plus a keyword reader, no network.

## Configuration

Environment variables for the API (see `.env.example`):

| Variable | Values | Default |
|---|---|---|
| `LLM_PROVIDER` | `mock`, `anthropic` | `mock` |
| `LLM_API_KEY` | key for the provider | none |
| `LLM_MODEL` | model id for the provider | `claude-sonnet-5-5` |
| `DEMO_MODE` | `true` saves the 3 personas under ids `lakshmi`, `ravi`, `shabana` | `true` |
| `LAABHMITRA_DB` | SQLite file path | `backend/laabhmitra.db` |

`gemini`, `openai` and `sarvam` are accepted names but not implemented yet; they fall back to mock.

## Layout

```
data/            scheme rules, personas, expected results, reference engine (do not edit)
backend/app/     engine/  llm/  pdf/  routers/  i18n/  models.py  store.py  main.py
backend/tests/   test_personas.py  test_engine.py  test_paths.py  test_guard.py  test_api.py
frontend/src/    pages/  components/  lib/  i18n/ (en, kn, hi)
AGENTS.md        the full spec
```

## Known limits

- Kannada and Hindi text was written without a native-speaker review. Check it before the demo.
- Scheme documents, application steps and status notes come straight from the data file
  and stay in English. The PDF pack is in English and writes rupees as "Rs.".
- Voice input uses the browser Web Speech API (Chrome or Edge, needs internet). Typing always works.
- Schemes marked "Check current status" or "Announced" must be re-checked on the official
  source before demo day.
- Out of scope: submitting applications, Aadhaar/DigiLocker, live scraping, lending or legal advice.
