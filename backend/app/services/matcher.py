from .resume_parser import extract_skills

def match_resume(resume_text: str, job_text: str) -> dict:
    resume = set(extract_skills(resume_text))
    required = set(extract_skills(job_text))
    matched = sorted(resume & required)
    missing = sorted(required - resume)
    score = round(len(matched) / len(required) * 100) if required else 0
    return {"score": score, "matched": matched, "missing": missing, "explanation": f"Matched {len(matched)} of {len(required)} detected job skills."}
