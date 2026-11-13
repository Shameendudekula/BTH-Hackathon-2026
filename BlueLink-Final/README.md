# BlueLink AI — Virtual Science Park (expanded hackathon prototype)

A working-code prototype for CAMPOR × BUILD 2026, Blue Science Park. Implements all six challenge service areas at prototype scope. The official challenge only requires at least three member profiles, two public opportunity sources and one or two convincingly demonstrated monitoring areas. This version additionally implements research/news, events, collaboration, member-change monitoring, alerts and staff insights. It is not a verified production service.

## Quick start (Windows / VS Code)

Extract the ZIP into a new directory; open `bluelink-full` in VS Code. Use Python 3.11–3.13. In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. Register a local username and password (12 characters minimum). Select Cleura, DNV Cyber or AFRY. No API key is required for deterministic profiling, matching, or the offline demonstration. Enable **Show simulated examples** to illustrate the research, news and events categories offline; these examples are explicitly synthetic, cannot be saved or rated and do not generate alerts. Funding/testing snapshots have public source links but are not live verified by the app until refreshed. Use a fresh database for this upgrade; old bearer-token workspaces are not migrated to accounts.

## Eight views

1. Company profile: baseline facts, evidence, inferred interests, private corrections, markets/geography/project notes; refresh one or all three sources.
2. Opportunity radar: categories Funding, Testing, Research, News, Events; rank by tags and declared interests; date/availability flags, explanations, citations, next action and bounded feedback.
3. Saved & feedback: workspace-specific persistence.
4. Assistant: scoped retrieval across categories and public partner suggestions, limited follow-up category context, refusals/clarifications, human referral. No general-purpose model generation or access to other accounts.
5. Quality & handover: evaluation guidance and limitations.
6. Collaboration: common capabilities and explicit complementary pairs, with public evidence and an introduction suggestion (no assumed willingness).
7. Monitoring & alerts: public profile changes, first-seen matched records, opt-in email digest.
8. Ecosystem insights: staff-only public technology counts and company-pair suggestions, not private workspace analytics.

## Enable live sources and optional AI

Click **Discover and refresh public opportunities** or **Refresh all sources and check changes**. These fetch public profiles and catalogue pages from company websites, Vinnova, RISE, Blue Science Park and Crossref metadata. Retrieval failures appear in diagnostics; successful earlier records are retained. A complete refresh can take time because multiple pages are retrieved sequentially. Respect website terms, robots policies and provider limits before deploying recurring collection. HTML connectors are heuristic, not guaranteed to extract every listing; a source returning no results is not proof that no opportunities exist.

Optional AI company extraction:

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
$env:OPENAI_MODEL="gpt-4o-mini"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Turn on **Use optional AI extraction** and refresh a profile. The LLM receives public page text only, in a structured extraction request. Exact supporting quotations must appear in the retrieved page text; claims still require human review. If the API fails or is unconfigured, extractive profiling is used. Never commit credentials. API billing is separate. The assistant intentionally remains deterministic rather than handing untrusted content or private profiles to a generative model.

## Staff access

Before starting Streamlit, set a strong unique invite secret:

```powershell
$env:BLUELINK_STAFF_INVITE="REPLACE_WITH_A_LONG_RANDOM_SECRET"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Create a new account with that invitation. Normal registrations get member role. The staff view only reads public records and does not reveal other workspaces. This is local password authentication with salted PBKDF2, not verified company identity, SSO, MFA or production authorization. Keep the database and server protected. Public deployments require TLS, rate limiting, secure account recovery, verified membership and role administration. Do not expose a staff invite publicly.

## Scheduling and email

The database is relative to the working directory. Run from the same folder as the dashboard:

```powershell
.\.venv\Scripts\python.exe refresh.py
```

This refreshes registered workspaces and updates in-app alerts. For recurring operation, use Windows Task Scheduler: create a daily task with the full path to `.venv\Scripts\python.exe` as Program, `refresh.py` as argument, and the project folder as Start in. No background process is created automatically. A server scheduler or cron can do the same on Linux. Configure scheduling only after verifying live sources; avoid aggressive polling. `BLUELINK_USE_AI=1` enables optional AI for scheduler runs.

Optional SMTP digest (STARTTLS provider on port 587):

```powershell
$env:BLUELINK_SMTP_HOST="smtp.example.com"
$env:BLUELINK_SMTP_PORT="587"
$env:BLUELINK_SMTP_FROM="alerts@example.com"
$env:BLUELINK_SMTP_USER="YOUR_SMTP_USER"
$env:BLUELINK_SMTP_PASSWORD="YOUR_SMTP_PASSWORD"
$env:BLUELINK_SEND_DIGEST="1"
```

Configure actual provider credentials in the process environment. In the dashboard, enter your email and opt in. Use Send pending digest or execute the scheduler with `BLUELINK_SEND_DIGEST=1`. Digests deduplicate successfully sent company/record IDs. Email address ownership is not verified by this prototype; production requires verified opt-in, unsubscribe/consent records and abuse prevention. No email is sent by default. Do not configure an external scheduler with secrets in command-line arguments.

## Architecture and source provenance

- `data.py`: three curated public company snapshots and funding/testing catalogue. Add additional vetted member records here and update the fixed allowlist in `live.py` for their official domains.
- `live.py`: allowlisted HTTPS fetching, bounded response sizes, public extractive/optional AI profiling, funding/testing discovery, source text hash, metadata and JSON-LD extraction.
- `extended.py`: Crossref research search, regional/provider event/news discovery, public-only collaboration, profile-change history, in-app alerts, SMTP, account authentication and scope-aware assistant.
- `core.py`: SQLite storage, date/status handling, deterministic ranking and baseline boundaries.
- `app.py`: Streamlit UI, account sessions, private refinements, recommendations, staff role gate.
- `refresh.py`: external scheduler entry point.
- `test_core.py`, `test_extended.py`: offline tests, including mocked network responses.

Sources: https://www.bluesciencepark.se/ (member directory, regional updates/events); https://cleura.com/; https://www.dnv.com/cyber/; https://afry.com/en/services; https://www.vinnova.se/en/ (funding and news); https://www.ri.se/en (testing and events); https://api.crossref.org/works (research metadata). Crossref metadata links to DOI records, not necessarily full text. Date extraction uses explicitly labelled dates or structured metadata. Event format and audience may remain unknown. News/event URLs are discovered heuristically; verify extracted pages are actual articles/events. No inferred company priorities are treated as confirmed facts.

Matching: technology overlap ×2, user interest overlap ×3, feedback ±1. Complementary pair rules supplement shared tags for partner suggestions. Scores are heuristic, not probabilities. Expired calls and past dated events are hidden by default. Missing dates and future dates do not prove current availability. Source changes compare page-content hashes (or fallback fact hashes); layout changes may produce false positives. First-seen alert does not mean newly published.

## Scale to 40+ members

The prototype ships with three member records. Add vetted member directory entries and official hosts to extend the same loops. For production, separate a shared public catalogue and source cache from private account data, use a job queue with per-host rate limits and retries, deduplicate retrieval across accounts, move to PostgreSQL with tenant authorization, introduce verified organization membership and audit logs, and add staff-reviewed taxonomy and source adapters. The current scheduler repeats collection per account and is not load-tested at 40+ companies. The staff view uses public snapshots in its own workspace, not a centralized real-time multi-tenant data warehouse.

## Remaining verification

Automated tests and compilation are run offline. Real provider API/HTML extraction, actual LLM calls, SMTP delivery, browser UI, scheduled task execution and human judgments of accuracy/relevance need runtime verification. Source content and availability can change; the offline snapshots are historical. No production security or full coverage guarantee is made. See EVALUATION.md and PITCH.md.

## Dashboard redesign

The dashboard now uses a dedicated Overview page, persistent sidebar navigation, a light navy/teal theme, workspace-specific KPI cards, opportunity category chart, top recommendations, and searchable opportunity results. Staff navigation remains role-restricted. Existing agents, database schema and tests are unchanged. The theme is stored in `.streamlit/config.toml`; presentation helpers are in `ui.py`. Launch from the project directory so Streamlit loads the theme. The redesign was compiled and the existing 26 tests passed; visual browser testing remains pending.

## Final edition: local startup and dashboard update

**Windows:** extract the ZIP fully, then double-click `START-BLUELINK.bat`. Python must be installed; first setup needs internet to install packages. Keep the console open. The launcher selects the first available port starting at 8501, binds only to 127.0.0.1, waits for Streamlit's health endpoint, and opens the browser. Use the exact printed address (it may be 8502 or another port). If the browser does not open, paste that address manually. If startup fails, the console displays the actual error.

Manual alternative from the extracted folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

The app and refresh script now resolve the database relative to their own project files. The overview has direct save actions, provenance/date details, refresh status, and quick navigation; the radar supports sorting. The sidebar has a dark navy theme. No external assets are required. The launcher is not a public deployment and cannot make localhost accessible outside your computer. If a corporate proxy or firewall blocks the local connection, check its loopback settings. Do not disable security software.
