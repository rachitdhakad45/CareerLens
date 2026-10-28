# CareerLens

CareerLens turns a text-based resume PDF into an explainable career plan. It extracts resume details and skills, suggests career families, provides ATS-oriented feedback, compares evidence with role requirements, recommends learning resources, and surfaces recently verified job listings.

## Requirements and setup

- Windows
- Python 3.12
- Git

Create a virtual environment and install the app dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Upload a text-based PDF under 10 MB and choose a target career family. Career-family predictions are suggestions, and you can select a different target. CareerLens does not save uploaded resumes or extracted profiles to its database.

## Career assistant

The assistant uses Gemini by default when a key is configured, and provides local, resume-grounded suggestions when no key is available or the service cannot respond. Set `GEMINI_API_KEY` in the server environment or Streamlit secrets before starting the app. `GOOGLE_API_KEY` is also accepted. Set `CAREERLENS_GEMINI_MODEL` to use a different available model; the default is `gemini-3.5-flash-lite` for lower latency.

For local Windows setup, create `.streamlit/secrets.toml` beside `config.toml` and add `GEMINI_API_KEY = "your-key"` (see `.streamlit/secrets.toml.example`). Restart Streamlit after saving. The real `secrets.toml` is ignored by Git and must never be committed. Create a key in [Google AI Studio](https://aistudio.google.com/apikey). For Streamlit Community Cloud, open the app's settings, paste the same TOML line into **Secrets**, save, and reboot the app. Streamlit documents local `st.secrets` and hosted secrets settings in its [secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

When configured, the career assistant uses Gemini by default and sends a compact career summary, recent chat messages, and the question to the external AI service. It does not send the original PDF, filename, email, or phone fields. Resume-derived text can still contain identifying details; the app discloses that a limited summary may be sent. If the service is unavailable, CareerLens falls back to a local suggestion. Chat history stays in the current Streamlit session and is not saved to the CareerLens database.

## Job listings and synchronization

The app reads recent listings from `data/careerlens.db` when available, or uses `data/opportunity_catalog.csv` as a fallback. In the Opportunities tab, listings match either normalized CareerLens role names or source-specific department labels connected through relevant skills. **Refresh job listings** starts a sync only when pressed. The standalone worker can be run separately:

```powershell
.\.venv\Scripts\python.exe .\scripts\run_opportunity_scheduler.py --interval 30
```

The worker runs once at startup and repeats at the selected interval. Keep one worker active for a source registry and database. Configure `CAREERLENS_DATABASE_URL` to use another SQLAlchemy-supported database. Sync outcomes are logged and stored per source in `sync_runs`. Listings are marked closed only when absent from two consecutive complete, non-empty successful snapshots.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Install the test dependency first with `python -m pip install -r requirements-dev.txt`. The suite covers resume analysis, recommendations, Greenhouse requests and retries, sync history, and stale-listing safeguards. Gemini requests are tested with mocked HTTP responses; tests do not require an API key.

## Current limits and deployment

- Image-only/scanned PDFs are not supported; the parser needs extractable text.
- ATS scores and skill coverage are advisory signals, not hiring predictions or measures of real-world proficiency.
- Job recommendations rank opportunities against skills not found in the resume; review the full listing and eligibility yourself.
- CareerLens has no sign-in, multi-user authorization, or saved resume history. A public deployment is a demo: uploaded PDFs are processed by the hosting server, and users should not upload confidential resumes. CareerLens does not save uploaded files or extracted profiles in its database. When configured, the career assistant sends a limited resume summary and question to an external AI service; this is disclosed in the app.
- The included SQLite database is local and intentionally excluded from Git. A hosted app starts with the CSV catalog and can sync listings when a user presses **Refresh job listings**. SQLite changes on a hosted instance are not a durable production store; configure a managed database through `CAREERLENS_DATABASE_URL` before relying on continuous listing history or scheduled syncs.
- `requirements.txt` is the deployment dependency file. For a public demo, create a public GitHub repository, then deploy `app.py` from that repository on Streamlit Community Cloud using Python 3.12. Add `GEMINI_API_KEY` in the host's Secrets settings to enable Gemini; never commit API keys or `.streamlit/secrets.toml`.
- The GitHub Actions workflow runs the test suite on pushes and pull requests. A green workflow confirms code checks only; the hosted app still needs a separate deployment and runtime check.
- Automatic application submission is not implemented. Users remain responsible for reviewing each listing and application.

Keep local databases, raw resume datasets, derived training data, and environment secrets out of Git.
