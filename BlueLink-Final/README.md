# BlueLink AI — Blekinge Innovation Radar
Hackathon prototype for Blue Science Park, CAMPOR × BUILD 2026. A live-first, evidence-led radar for companies with limited time for market and technology scouting. The latest challenge documents and organizer guidance shape this version: regional relevance, official member directory, one company login, Ymner discovery and a concise weekly briefing.

## Quick start (Windows)
Extract this archive. Open `BlueLink-Final` in VS Code. Python 3.12 recommended. In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
$env:BLUELINK_STAFF_INVITE="replace-with-a-long-random-secret"
.\.venv\Scripts\python.exe launch.py
```

The launcher opens the actual loopback address (usually http://127.0.0.1:8501), selects another port if needed, and keeps the console running. Do not close it while using the application. Alternatively run `python -m streamlit run app.py` in the virtual environment.

### First login and company onboarding
1. Configure `BLUELINK_STAFF_INVITE` before startup. Use a strong unique secret; never commit it.
2. Open Staff registration; create a staff username and password (12–256 characters) using that invitation. Sign in.
3. For the three-company demonstration, skip full directory discovery: Cleura, DNV Cyber and AFRY are already available. For future expansion, open Ecosystem insights → Discover official members. The crawler follows official public member detail links, including related member links and visible pagination. It retains successful records and reports errors/coverage uncertainty. If the directory's Load more UI hides additional links, staff may enter additional official member detail URLs (one per line). Check coverage against the directory; members and partners are not necessarily distinguished by every page.
4. Staff provisions a username and password for each company in Ecosystem insights. The database enforces one account per company ID. Share initial credentials securely. Sign out and sign in with that company account. The member account cannot switch to another company's workspace or provision another company.
5. Select Company profile to review facts, original evidence, inferred interests and private corrections. Refresh the selected profile to retrieve its source. Refine priorities, then open Opportunity radar or Overview. Compare results using separately provisioned company accounts.

This version uses a new `company_accounts` table; old individually registered accounts are not migrated. Existing public data may be retained, but old private workspaces are not transferred automatically. Use a clean database for the demonstration or migrate with an authorized operator.

## Live data and the weekly brief
The Overview shows up to five actionable matches, why each fits, relevant source/retrieval/deadline information and a concrete next action. The radar contains Funding, Testing, Research, News and Events. The collaboration view uses public profiles and regional proximity. Public findings and public profiles are shared across accounts; private refinements, saved items, feedback and alert settings are company-bound. Staff insights use public information only.

After sign-in, a bounded background worker within the running Streamlit process checks public sources when the workspace's last refresh attempt is more than six hours old; the interface polls for completion. Manual Refresh live sources now is available. This is not an unattended cloud scheduler. The prior successful records remain available if a connector fails. Historical snapshots and explicitly synthetic examples are separate opt-in modes, disabled by default. Source dates and status are not proof of present availability.

## Public sources and agent roles
- `regional.py`: member discovery and directory field extraction (city, industry, employee band, website), shared public profile storage, staff-provisioned company accounts, local relevance and briefing.
- `live.py`: allowlisted HTTPS retrieval, extractive company profile generation, optional LLM fact extraction with exact supporting quotations, funding/testbed pages and source hashes. The three initial seed company websites are approved. Directory-listed external company sites are displayed but only fetched if their host is preapproved; set `BLUELINK_APPROVED_HOSTS` to comma-separated reviewed hostnames before startup. Review each host before adding it; no arbitrary user-supplied URLs are fetched. Public directory evidence remains available without external website approval. Missing or uncertain fields are labelled.
- `funding.py`: Ymner discovery link and staff-authorized CSV import (`official_url` header), or pasted original funder call links. Only approved call-page URLs are retrieved; official call information, not aggregator text, is used for the finding. An optional public-link adapter is disabled by default; enable `BLUELINK_YMNER_PUBLIC_ALLOWED=1` only after verifying permission. It extracts direct original funder links visible in public HTML, not a private API or entire catalogue. If none are exposed, use authorized export or manual original links. Vinnova and RISE connectors operate independently. Additional funder hosts need explicit operator approval and adapter/path review.
- `extended.py`: Crossref metadata, provider news/events, collaboration, public change detection, notification records, bounded assistant and email support. Research query themes are derived from public company technology tags (fallback themes when unavailable). Never send private refinements to external services.
- `core.py`: SQLite and deterministic matching. A technology match contributes 2 points, a declared interest 3 points and feedback ±1. Physical local events/testing and partners get +3 Karlskrona or +2 other named Blekinge location; online/hybrid access receives no proximity adjustment. Unknown locations receive zero. No geographic adjustment for funding/research/news, and geography never creates a match by itself. Scores are heuristic, not probabilities. Past dated events and expired calls are hidden by default.
- `dynamic.py`: live-first catalogue, refresh timing and bounded worker queue; `deployment.py`: configurable database path; `app.py` and `ui.py`: Streamlit presentation.

Source starting points: https://www.bluesciencepark.se/bli-medlem/ ; https://www.ymner.com/en/find-financing/grants?status=coming&status=open ; https://www.vinnova.se/en/ ; https://www.ri.se/en ; https://api.crossref.org/works . All actual findings include source URLs and retrieval dates. Event dates/locations and grant eligibility are conservative and must be verified with the organizer/funder.

## Optional AI and email
Set `OPENAI_API_KEY` and `OPENAI_MODEL=gpt-4o-mini` in the process environment; enable optional AI extraction in the sidebar. Only public page text is sent. Model claims must include exact quotations; this checks source traceability, not entailment. Failure falls back to extraction. The restricted assistant is deterministic category retrieval, not a general-purpose LLM. It handles supported requests, unrelated requests, overrides, private-data requests, unclear requests and human eligibility/commitment referrals. External content is evidence, never instructions.

For SMTP, configure `BLUELINK_SMTP_HOST`, `BLUELINK_SMTP_PORT=587`, `BLUELINK_SMTP_FROM`, `BLUELINK_SMTP_USER`, `BLUELINK_SMTP_PASSWORD`; a member must opt in inside Monitoring & alerts. `BLUELINK_SEND_DIGEST=1` enables scheduler delivery. Only company-bound alerts are sent. Email ownership verification and production unsubscribe/consent controls remain future work; use test addresses for the hackathon. Do not enable email on a public demo without verification/abuse controls.

## Deployment and scheduled collection
See DEPLOY.md. On Render set Root Directory to `BlueLink-Final`, use the provided Streamlit start command and configure the staff secret. Set `BLUELINK_DB_PATH` to an appropriate persistent location if hosting supports it. Free Render disk storage is ephemeral; use no sensitive production data. `python refresh.py` refreshes provisioned accounts; configure an external scheduler for unattended updates. Shared catalogue merges are atomic, but source fetching is still repeated per account; production should add centralized scheduling and caching.

## Verification and limitations
Run `python -m unittest -v` (45 tests in this package) and `python -m compileall -q .`. The original and new tests cover software behavior, using mocked network fixtures where applicable. No live browser, provider requests, full 40+ directory coverage, real OpenAI calls, SMTP delivery or human relevance evaluation has been confirmed in the packaging environment. The official hackathon scope requires three public profiles, two information sources and one working journey, not verified coverage of every member. This project includes all monitoring areas as prototype adapters, not guaranteed complete source coverage. Use EVALUATION.md for the acceptance protocol and PITCH.md for the Sunday demo. Production requires validated membership identity, secure account recovery, rate limiting, MFA/SSO, centralized caching/authorization, verified privacy controls, and real human evaluation.

## Three-company final release
This archive intentionally ships only Cleura, DNV Cyber and AFRY as initial company records. Staff may discover additional members later; to keep the demo at three, do not run directory discovery. An existing expanded database is not silently deleted or filtered; use a new database path for a clean three-company demonstration. The original organizer documents are intentionally excluded from this distribution. Their requirements are retained in the implementation, the checklist below and EVALUATION.md. Follow `DEPLOY.md` for the existing Render service.

## Organizer requirements retained in this release
- Intended users: small companies (approximately 10–25 employees) with limited market-scanning resources. The weekly brief provides up to five relevant findings, evidence, uncertainty and concrete next actions.
- Prototype scope: three initial profiles, at least two distinct public opportunity sources and one end-to-end personalized journey. The wider service targets the official 40+ Blue Science Park member directory; full coverage is not claimed.
- Profiles: public website retrieval, sourced facts distinct from inferred interests, retrieval dates, uncertainty and editable private refinements. One staff-provisioned login per company; no cross-company private profile access.
- Discovery: public funding, testing, research, news and event sources; Ymner for funding discovery through authorized imports and original funder URL verification.
- Ranking: company-specific technology and priority matches, bounded feedback, and regional preference for relevant physical opportunities and partners (+3 Karlskrona, +2 other named Blekinge locations). Online and hybrid events have no geographic penalty; location alone does not establish relevance.
- Presentation: distinct company rankings, explanations, evidence links, deadlines where verified, actionable next steps and clear labels for historical and simulated findings.
- Boundaries: restricted relevant questions, refusal of unrelated requests and instruction overrides, private-data isolation, clarification and human referral for formal eligibility.
- Demonstration: show public website to profile, change a priority, show a relevant actionable result and demonstrate a boundary holding. Deliver working code, setup, evaluation and handover.
- Evaluation: use EVALUATION.md for automated tests, manual source validation, relevance and privacy checks. Do not claim measured accuracy, time savings or production readiness without evidence.
