import re
from pathlib import Path
from typing import Iterable
import docx
import pdfplumber

SKILLS = {"python","javascript","typescript","react","nextjs","node","nodejs","sql","postgresql","mongodb","aws","docker","kubernetes","git","api","graphql","excel","figma","java","fastapi","frontend","backend","testing","machine learning","data analysis"}

def read_resume(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".txt", ".md"}:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        return "\n".join(p.text for p in docx.Document(path).paragraphs)
    if suffix == ".pdf":
        with pdfplumber.open(path) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    return ""

def extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(skill for skill in SKILLS if re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", lowered))

def job_skills(text: str) -> list[str]:
    return extract_skills(text)
