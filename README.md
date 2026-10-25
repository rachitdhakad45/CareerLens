# CareerLens

AI-powered career intelligence platform for resume analysis, skill extraction, career prediction, and opportunity recommendations.

## Requirements

- Windows
- Python 3.12
- Git

## Run the application

Open PowerShell in the CareerLens folder and run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Run the opportunity scheduler

```powershell
.\.venv\Scripts\python.exe .\scripts\run_opportunity_scheduler.py
```

The scheduler runs while its process is active and defaults to a 30-minute interval.

## Data and security

Keep local databases, raw resume datasets, derived training data, and environment secrets out of Git.
