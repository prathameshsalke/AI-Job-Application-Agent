# AI Job Application Agent

A runnable, safety-first MVP for managing job applications.

## Features

- JWT registration and login
- Persistent SQLite database (PostgreSQL-compatible configuration)
- Candidate profile storage
- PDF, DOCX, and TXT resume parsing
- Explainable resume/job matching
- Job analysis and blocker detection
- Application tracker
- Excel export
- Browser extension page extraction
- Review-before-submit approval gate

The application never bypasses CAPTCHA, bot protection, authentication, or security controls. It does not submit an application unless the user explicitly approves it.

## Requirements

- Python 3.11+
- VS Code
- Optional: Docker

## Run in VS Code

### Backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

uvicorn app.main:app --reload --port 8000
```

Open API docs at http://localhost:8000/docs.

### Frontend

In a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Open http://localhost:5500.

Register a user in the UI, upload resumes, add a job, match resumes, and create an application. The UI stores the JWT in browser local storage.

### Chrome extension

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Choose Load unpacked.
4. Select the repository `extension` directory.
5. Open a job page and click the extension.

Set the backend URL in the extension popup if needed; the default is `http://localhost:8000`.

### Docker

```bash
docker compose up --build
```

- API: http://localhost:8000
- UI: http://localhost:3000

## API workflow

1. `POST /api/auth/register`
2. `POST /api/auth/login`
3. `POST /api/profile`
4. `POST /api/resumes` with multipart field `file`
5. `POST /api/jobs`
6. `POST /api/jobs/{job_id}/matches`
7. `POST /api/applications` with `approved: false` to create a review record
8. `POST /api/applications/{id}/approve` only after user review
9. `GET /api/export/applications.xlsx`

## Production work still recommended

- Store resume files in encrypted object storage.
- Add Google Drive/Sheets OAuth integration.
- Add site-specific browser adapters only for permitted sites.
- Add a queue for long-running parsing and browser tasks.
- Add malware scanning, audit logs, rate limiting, MFA, and comprehensive tests.
