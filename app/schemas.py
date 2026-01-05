from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import Role


class DepartmentCreate(BaseModel):
    name: str = Field(..., description="部门名称")


class DepartmentOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    display_name: str
    role: Role
    department_id: Optional[int] = None


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: Role
    department_id: Optional[int]

    class Config:
        from_attributes = True


class ScaleItemCreate(BaseModel):
    prompt: str
    field_type: str = "single_choice"
    options: Optional[str] = None


class ScaleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    logic: Optional[str] = None
    items: List[ScaleItemCreate]


class ScaleItemOut(ScaleItemCreate):
    id: int

    class Config:
        from_attributes = True


class ScaleOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    logic: Optional[str]
    items: List[ScaleItemOut]

    class Config:
        from_attributes = True


class PatientCreate(BaseModel):
    name: str


class PatientOut(BaseModel):
    id: int
    name: str
    department_id: int
    user_id: int

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    patient_id: int
    scale_id: int
    allow_patient_view: bool = False
    report_header: Optional[str] = None
    evaluation_date: Optional[datetime] = None


class AssignmentOut(BaseModel):
    id: int
    patient_id: int
    scale_id: int
    allow_patient_view: bool
    report_header: Optional[str]
    evaluation_date: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True


class AssignmentReportSettings(BaseModel):
    allow_patient_view: Optional[bool] = None
    report_header: Optional[str] = None


class ResponseCreate(BaseModel):
    item_id: int
    answer_text: str


class ResponseSubmission(BaseModel):
    responses: List[ResponseCreate]
    duration_seconds: Optional[int] = None


class AssignmentDetail(AssignmentOut):
    scale: ScaleOut
    responses: List[ResponseCreate] = []
