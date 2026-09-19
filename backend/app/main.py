import csv
from pathlib import Path
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import User, Profile, Resume, Job, Match, Application
from .schemas import RegisterRequest, LoginRequest, ProfileRequest, JobRequest, ApplicationRequest
from .security import hash_password, verify_password, token_for, current_user
from .services.resume_parser import read_resume, extract_skills, job_skills
from .services.matcher import match_resume

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AI Job Application Agent API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url, "http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/api/auth/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == str(data.email)).first(): raise HTTPException(409, "Email already registered")
    user = User(full_name=data.full_name, email=str(data.email), password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": token_for(user.email), "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

@app.post("/api/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email)).first()
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    return {"token": token_for(user.email), "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

@app.get("/api/profile")
def get_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"data": db.query(Profile).filter(Profile.user_id == user.id).first()}

@app.post("/api/profile")
def save_profile(data: ProfileRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile: profile = Profile(user_id=user.id); db.add(profile)
    for key, value in data.model_dump().items(): setattr(profile, key, value)
    db.commit(); db.refresh(profile)
    return {"data": profile}

@app.post("/api/resumes")
def upload_resume(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    allowed = {".pdf", ".docx", ".txt", ".md"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed: raise HTTPException(400, "Only PDF, DOCX, TXT, and MD files are supported")
    stored = Path(settings.upload_dir) / f"{user.id}-{len(db.query(Resume).filter(Resume.user_id == user.id).all())}-{Path(file.filename).name}"
    stored.write_bytes(file.file.read())
    text = read_resume(str(stored))
    resume = Resume(user_id=user.id, original_name=file.filename, stored_path=str(stored), text=text, skills=",".join(extract_skills(text)))
    db.add(resume); db.commit(); db.refresh(resume)
    return {"data": {"id": resume.id, "name": resume.original_name, "skills": resume.skills.split(",") if resume.skills else []}}

@app.get("/api/resumes")
def list_resumes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.created_at.desc()).all()
    return {"data": [{"id": r.id, "name": r.original_name, "skills": r.skills.split(",") if r.skills else [], "created_at": r.created_at} for r in rows]}

@app.post("/api/jobs")
def create_job(data: JobRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lowered = data.description.lower()
    blocker = next((x for x in ["captcha", "verify you are human", "access denied", "bot detected", "rate limit"] if x in lowered), "")
    job = Job(user_id=user.id, url=str(data.url), title=data.title, company=data.company, location=data.location, description=data.description, skills=",".join(job_skills(data.description)), blocker=blocker)
    db.add(job); db.commit(); db.refresh(job)
    return {"data": {"id": job.id, "title": job.title, "company": job.company, "skills": job.skills.split(",") if job.skills else [], "blocker": job.blocker}}

@app.get("/api/jobs")
def list_jobs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"data": db.query(Job).filter(Job.user_id == user.id).order_by(Job.created_at.desc()).all()}

@app.post("/api/jobs/{job_id}/matches")
def calculate_matches(job_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user.id).first()
    if not job: raise HTTPException(404, "Job not found")
    rows = []
    for resume in db.query(Resume).filter(Resume.user_id == user.id).all():
        result = match_resume(resume.text, job.description)
        rows.append({"resume_id": resume.id, "resume_name": resume.original_name, **result})
        db.add(Match(user_id=user.id, job_id=job.id, resume_id=resume.id, score=result["score"], matched=",".join(result["matched"]), missing=",".join(result["missing"]), explanation=result["explanation"]))
    db.commit()
    return {"data": sorted(rows, key=lambda x: x["score"], reverse=True), "blocked": job.blocker}

@app.post("/api/applications")
def create_application(data: ApplicationRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == data.job_id, Job.user_id == user.id).first(); resume = db.query(Resume).filter(Resume.id == data.resume_id, Resume.user_id == user.id).first()
    if not job or not resume: raise HTTPException(404, "Job or resume not found")
    status = "submitted" if data.approved and not job.blocker else "awaiting_review"
    notes = data.notes or (f"Blocked: {job.blocker}" if job.blocker else "Review required before submission")
    app_record = Application(user_id=user.id, job_id=job.id, resume_id=resume.id, status=status, notes=notes)
    db.add(app_record); db.commit(); db.refresh(app_record)
    return {"data": {"id": app_record.id, "status": status, "notes": notes}}

@app.post("/api/applications/{application_id}/approve")
def approve_application(application_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = db.query(Application).filter(Application.id == application_id, Application.user_id == user.id).first()
    if not record: raise HTTPException(404, "Application not found")
    job = db.query(Job).filter(Job.id == record.job_id).first()
    if job.blocker: raise HTTPException(409, f"Cannot approve: {job.blocker}")
    record.status = "submitted"; db.commit(); return {"data": {"id": record.id, "status": record.status}}

@app.get("/api/applications")
def list_applications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"data": db.query(Application).filter(Application.user_id == user.id).order_by(Application.created_at.desc()).all()}

@app.get("/api/export/applications.csv")
def export_applications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    path = Path("applications-export.csv")
    rows = db.query(Application).filter(Application.user_id == user.id).all()
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output); writer.writerow(["id", "job_id", "resume_id", "status", "notes", "created_at"])
        for row in rows: writer.writerow([row.id, row.job_id, row.resume_id, row.status, row.notes, row.created_at])
    return FileResponse(path, media_type="text/csv", filename="applications.csv")
