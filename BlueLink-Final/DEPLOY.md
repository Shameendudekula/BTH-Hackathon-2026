# Render deployment — Blekinge edition
Use the existing team repository `Shameendudekula/BTH-Hackathon-2026`. Replace contents of its `BlueLink-Final` folder with the extracted archive folder contents, including `.streamlit/config.toml` and `.gitignore`. Do not nest another folder. Keep unrelated repository content. Commit to the existing Dhara092005-patch-1 branch and configure the existing Render service to deploy that branch, if the team intends to leave main unchanged. This archive is not automatically pushed.

| Setting | Value |
|---|---|
| Root Directory | BlueLink-Final |
| Branch | Dhara092005-patch-1 (for branch-only deployment) |
| Runtime | Python 3 |
| Build | pip install -r requirements.txt |
| Start | python -m streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true |
| Health | /_stcore/health |
| PYTHON_VERSION | 3.12.10 |
| BLUELINK_STAFF_INVITE | strong private random secret (required for staff bootstrap) |
| OPENAI_MODEL | gpt-4o-mini (optional) |
| OPENAI_API_KEY | optional private key |

Set secrets in Render Environment, never GitHub. `BLUELINK_APPROVED_HOSTS` may contain reviewed official company/funder hostnames. Leave Ymner automatic scraping disabled unless permission is established. With Auto-Deploy On Commit, pushing to the configured deployment branch should trigger a build; otherwise Manual Deploy → Deploy latest commit. Confirm build and health endpoint, then open the actual service URL from Render. A health response does not prove all pages or connectors work.

Free service SQLite is ephemeral. For a paid persistent disk mount `/var/data`, set `BLUELINK_DB_PATH=/var/data/bluelink.sqlite3`. Back up and protect the data. The nested render.yaml is a configuration reference; manual service settings above are sufficient for the existing service. Do not use launch.py on Render (local loopback launcher). Unattended refresh needs an external scheduler with access to the same database; avoid concurrent full refreshes in production.

First sign in through Staff registration using the configured invitation; provision three company logins and test each before demo. Old individual account rows are not migrated. Use new accounts. Verify the theme, all sections, live retrieval diagnostics, company isolation and local ranking.

## Three-company release
The three initial companies are Cleura, DNV Cyber and AFRY. Use a fresh database (e.g. `BLUELINK_DB_PATH=/tmp/bluelink-three.sqlite3` on the free demo service) if you previously imported expanded records. This creates a new workspace database and does not erase the old one. Re-provision the three accounts; do not run full member discovery for the three-company demo. On a paid persistent disk use a new filename under the disk mount instead.
