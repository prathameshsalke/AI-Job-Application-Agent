from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl, Field

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    location: str = ""
    education: str = ""
    experience: str = ""
    linkedin: str = ""
    github: str = ""
    work_authorization: str = ""

class JobRequest(BaseModel):
    url: HttpUrl
    title: str = "Unknown role"
    company: str = "Unknown company"
    location: str = ""
    description: str = Field(min_length=20)

class ApplicationRequest(BaseModel):
    job_id: int
    resume_id: int
    notes: str = ""
    approved: bool = False
