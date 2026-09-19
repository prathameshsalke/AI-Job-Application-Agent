# AI Job Application Agent

A safety-first job application assistant prototype.

## Run locally

### UI only
Open `frontend/index.html` directly, or run:

```bash
cd frontend
python -m http.server 5500
```

Visit http://localhost:5500.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Docker

```bash
docker compose up --build
```

## Workflow

1. Create a candidate profile.
2. Upload one or more resumes.
3. Paste a job URL and description.
4. Compare resumes using an explainable job-match score.
5. Review extracted information and application fields.
6. Stop for CAPTCHA, login, bot detection, or ambiguity.
7. Require explicit user approval before submission.
8. Track the result and export application records.

This repository intentionally does not bypass CAPTCHA, bot protection, authentication, or website security controls.
