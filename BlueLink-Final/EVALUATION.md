# Evaluation and acceptance checklist

The authoritative challenge is the uploaded four-page Blue Science Park Virtual Science Park brief. It requires a working flow from discovery to a personalized result, at least three public company profiles, two public opportunity sources, evidence/fact-inference separation, editable profiles, distinct rankings, dated sources, bounded interaction and labelled simulations. It permits one or two monitoring categories; this expanded prototype adds every service area.

## Offline automated evaluation

Run `python -m unittest -v` and `python -m compileall -q .`. Original tests cover profile evidence, two providers, different rankings, refinements, expired funding, scope, storage isolation, allowlist, deadline extraction, mocked live profile and discovery, AI fallback, feedback, and untrusted webpage text. Extended tests cover password verification/roles, account isolation, collaboration provenance, event dates, profile changes, alert deduplication, simulation labelling, assistant scope/follow-up, mocked Crossref, email opt-in and catalogue deduplication. These tests measure software behavior, not real-world extraction accuracy.

## Manual acceptance procedure

| Check | Method | Pass criterion |
|---|---|---|
| Profile accuracy | Review three company pages and sample five claims each | Each supported claim matches its source; uncertainty and corrections marked |
| Relevance | Have company representative rate top five results before/after refinement | Record ratings and compare precision@5; do not invent numbers |
| Traceability | Open every top result link and compare date/evidence | URL works, date correct or explicitly unknown |
| Live research | Refresh Crossref | At least one DOI record with verifiable metadata, or clear connector diagnostic |
| Live news/events | Refresh providers | Verify actual article/event page, date, audience and format; record false positives |
| Funding/testing | Refresh Vinnova and RISE | Verify deadline, access and eligibility; no closed call promoted |
| Collaboration | Compare Cleura with other companies | Shared/complementary capabilities explained; no private data or confirmed intent claimed |
| Public changes | Refresh two snapshots with changed source content | Change history shows before/after evidence without claiming a strategic shift |
| Alerts | Refresh matching results twice | One alert per company/record, simulation excluded |
| Email | Use opted-in test mailbox and configured SMTP | First send delivered, duplicate refresh does not resend |
| Privacy | Register two users and a staff user | No cross-account private refinements, notes, saved records or chat |
| Boundaries | Ask for funding, research, partners, unrelated poem, instruction override and private profile | Relevant sources; redirect/refuse out-of-scope; human referral for commitments |
| Browser | Launch Streamlit, navigate every tab, sign out/re-login | No runtime exceptions, state persists |
| Scheduling | Execute refresh.py and configure a local daily task | Diagnostics recorded, task runs under correct working directory |

Document actual test outcomes during demo rehearsal. No human accuracy/relevance percentage is claimed.

## Known limitations

Three member seed records, no full directory crawl or 40-member load test. Public HTML changes and blocked requests can reduce coverage. Event/news detection is heuristic and publication dates may be missing. Only selected Crossref query themes are covered. Optional AI quotes are checked verbatim, but entailment is not guaranteed. Assistant uses bounded keyword/category retrieval, not general conversational reasoning. Account identity is not verified as a real company representative; production TLS, rate limits, SSO, MFA and role management are absent. Scheduled execution and email require external configuration. Staff insights use public data in the staff workspace only. Simulated examples are separate from live records.

## Final launcher and dashboard checks

29 automated tests passed (26 existing tests plus 3 launcher tests: occupied port fallback, exhausted range, and unavailable health endpoint). Python compilation passed. These tests do not replace an actual Streamlit browser run. Streamlit installation in the packaging environment failed due to unavailable network/DNS, so Windows batch execution and live browser verification remain outstanding. The user's original localhost failure has not been reproduced; the launcher addresses common startup and port-selection problems without claiming a verified diagnosis.
