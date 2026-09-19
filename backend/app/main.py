from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from pathlib import Path
from datetime import datetime
import re
import uuid

app = FastAPI(title="AI Job Application Agent API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOADS = Path("uploads")
UPLOADS.mkdir(exist_ok=True)
resumes = []
jobs = []
applications = []

SKILLS = {"python","javascript","typescript","react","nextjs","node","nodejs","sql","postgresql","mongodb","aws","docker","kubernetes","git","api","graphql","excel","figma","java","fastapi","frontend","backend","testing"}

class JobRequest(BaseModel):
    url: HttpUrl
    title: str = "Unknown role"
    company: str = "Unknown company"
    location: str = "Unknown location"
    description: str

class ApplicationRequest(BaseModel):
    job_id: str
    resume_id: str
    approved: bool = False

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/resumes")
async def upload_resume(file: UploadFile = File(...)):
    resume_id = str(uuid.uuid4())
    path = UPLOADS / f"{resume_id}-{file.filename}"
    path.write_bytes(await file.read())
    text = path.read_text(errors="ignore") if path.suffix.lower() in {".txt", ".md"} else "Resume uploaded; PDF/DOCX extraction can be enabled in production."
    found = sorted({skill for skill in SKILLS if re.search(rf"\\b{re.escape(skill)}\\b", text.lower())})
    record = {"id": resume_id, "name": file.filename, "skills": found, "created_at": datetime.utcnow().isoformat()}
    resumes.append(record)
    return {"data": record}

@app.get("/api/resumes")
def list_resumes():
    return {"data": resumes}

@app.post("/api/jobs")
def create_job(payload: JobRequest):
    job_id = str(uuid.uuid4())
    words = set(re.findall(r"[a-zA-Z][a-zA-Z+#.-]+", payload.description.lower()))
    skills = sorted(SKILLS.intersection(words))
    blocked_terms = ["captcha", "verify you are human", "access denied", "bot detected"]
    blocked = next((term for term in blocked_terms if term in payload.description.lower()), None)
    record = {"id": job_id, **payload.model_dump(mode="json"), "skills": skills, "blocked": blocked, "created_at": datetime.utcnow().isoformat()}
    jobs.append(record)
    return {"data": record}

@app.get("/api/jobs")
def list_jobs():
    return {"data": jobs}

@app.post("/api/jobs/{job_id}/match")
def match_resumes(job_id: str):
    job = next((item for item in jobs if item["id"] == job_id), None)
    if not job:
        return {"error": "Job not found"}
    results = []
    required = set(job["skills"])
    for resume in resumes:
        matched = sorted(required.intersection(resume["skills"]))
        missing = sorted(required.difference(resume["skills"]))
        score = round((len(matched) / len(required)) * 100) if required else 0
        results.append({"resume_id": resume["id"], "resume_name": resume["name"], "score": score, "matched": matched, "missing": missing})
    return {"data": sorted(results, key=lambda item: item["score"], reverse=True)}

@app.post("/api/applications")
def create_application(payload: ApplicationRequest):
    if not payload.approved:
        return {"status": "awaiting_approval", "message": "Explicit user approval is required before submission."}
    record = {"id": str(uuid.uuid4()), **payload.model_dump(), "status": "submitted", "created_at": datetime.utcnow().isoformat()}
    applications.append(record)
    return {"data": record}

@app.get("/api/applications")
def list_applications():
    return {"data": applications}
