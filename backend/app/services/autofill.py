"""Autofill helpers for job application forms.

This is intentionally safety-first: it fills common form fields from the saved
profile and selected resume, but never auto-submits unless the user approves.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _profile_payload(profile: Any) -> dict:
    if profile is None:
        return {}
    return {
        "first_name": _normalize(getattr(profile, "first_name", "")),
        "last_name": _normalize(getattr(profile, "last_name", "")),
        "full_name": _normalize(getattr(profile, "first_name", "")) + " " + _normalize(getattr(profile, "last_name", "")).strip()).strip(),
        "email": _normalize(getattr(profile, "email", "")),
        "phone": _normalize(getattr(profile, "phone", "")),
        "location": _normalize(getattr(profile, "location", "")),
        "education": _normalize(getattr(profile, "education", "")),
        "experience": _normalize(getattr(profile, "experience", "")),
        "linkedin": _normalize(getattr(profile, "linkedin", "")),
        "github": _normalize(getattr(profile, "github", "")),
        "work_authorization": _normalize(getattr(profile, "work_authorization", "")),
    }


def _resume_summary(resume_text: str) -> dict:
    text = _normalize(resume_text)
    # Conservative summary for form filling; not a full extraction engine.
    return {
        "summary": text[:500],
        "skills": re.findall(r"[A-Za-z+#.-]+", text)[:30],
    }


def autofill_job_page(job_url: str, resume_path: str, profile: Any, resume_text: str) -> dict:
    """Fill common fields on a job application page.

    This is intentionally limited. It tries common selectors and never submits
    the form automatically. The safety rule is preserved: the app shows the user
    the result before final approval and submit.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        ) from exc

    profile_data = _profile_payload(profile)
    resume_data = _resume_summary(resume_text)

    payload = {
        "job_url": job_url,
        "status": "ready_for_review",
        "blocked": False,
        "filled_fields": [],
        "notes": "Autofill prepared for human review before submit.",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            payload["blocked"] = True
            payload["status"] = "blocked"
            payload["notes"] = "Could not load the job page. The site may require login or bot protection."
            return payload

        title = (page.title() or "").lower()
        page_text = (page.locator("body").inner_text() or "").lower()
        if any(token in title or token in page_text for token in ["captcha", "verify you are human", "security check", "access denied", "bot detected"]):
            payload["blocked"] = True
            payload["status"] = "blocked"
            payload["notes"] = "The page looks blocked by bot protection or login requirements."
            return payload

        field_map = {
            "first_name": ["first name", "firstname", "given name"],
            "last_name": ["last name", "lastname", "family name", "surname"],
            "full_name": ["full name", "name", "your name"],
            "email": ["email", "e-mail"],
            "phone": ["phone", "mobile", "telephone"],
            "location": ["location", "city", "address"],
            "work_authorization": ["work authorization", "visa status", "citizenship"],
        }

        key_values = {
            "first_name": profile_data.get("first_name", ""),
            "last_name": profile_data.get("last_name", ""),
            "full_name": profile_data.get("full_name") or (f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()),
            "email": profile_data.get("email", ""),
            "phone": profile_data.get("phone", ""),
            "location": profile_data.get("location", ""),
            "work_authorization": profile_data.get("work_authorization", ""),
        }

        for field_key, possible_labels in field_map.items():
            value = key_values.get(field_key, "")
            if not value:
                continue
            selector = None
            for label in possible_labels:
                selector = (
                    f"input[name*='{label}' i], "
                    f"input[id*='{label}' i], "
                    f"input[placeholder*='{label}' i], "
                    f"textarea[name*='{label}' i], "
                    f"textarea[id*='{label}' i]"
                )
                if page.locator(selector).count() > 0:
                    break
            if selector and page.locator(selector).count() > 0:
                page.locator(selector).first.fill(value)
                payload["filled_fields"].append(field_key)

        # Best-effort resume file upload
        resume_file = Path(resume_path)
        if resume_file.exists():
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                file_input.first.set_input_files(str(resume_file))
                payload["filled_fields"].append("resume")

        # Additional generic "description" or "cover letter" text hint
        cover_selector = "textarea[name*='cover' i], textarea[id*='cover' i], textarea[name*='message' i], textarea[id*='message' i]"
        if page.locator(cover_selector).count() > 0 and resume_data.get("summary"):
            page.locator(cover_selector).first.fill(resume_data["summary"][:800])
            payload["filled_fields"].append("cover_letter")

        browser.close()

    payload["status"] = "ready_for_review" if not payload["blocked"] else "blocked"
    if not payload["filled_fields"]:
        payload["notes"] = "No common application fields were recognized on the page. Review is required."
    return payload


__all__ = ["autofill_job_page"]
