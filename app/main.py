from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, get_db
from .models import (
    Base,
    Department,
    Patient,
    Role,
    Scale,
    ScaleAssignment,
    ScaleItem,
    ScaleResponse,
    User,
)
from .schemas import (
    AssignmentCreate,
    AssignmentDetail,
    AssignmentOut,
    AssignmentReportSettings,
    DepartmentCreate,
    DepartmentOut,
    PatientCreate,
    PatientOut,
    ResponseSubmission,
    ScaleCreate,
    ScaleOut,
    UserCreate,
    UserOut,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="心理测评综合管理系统 API")


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> User:
    if not x_user_id or not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证头: X-User-Id 与 X-User-Role",
        )

    user = db.query(User).filter(User.id == x_user_id).first()
    if not user or user.role != x_user_role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或角色不匹配")
    return user


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/admin/departments", response_model=DepartmentOut)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    department = Department(name=payload.name)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@app.post("/admin/departments/{department_id}/admins", response_model=UserOut)
def create_department_admin(
    department_id: int,
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    if payload.role != Role.DEPARTMENT_ADMIN:
        raise HTTPException(status_code=400, detail="部门管理员必须使用 department_admin 角色")

    department = db.query(Department).get(department_id)
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")

    user = User(
        username=payload.username,
        display_name=payload.display_name,
        role=payload.role.value,
        department_id=department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/admin/scales", response_model=ScaleOut)
def create_scale(payload: ScaleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Role.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="只有超级管理员可以创建量表")

    scale = Scale(name=payload.name, description=payload.description, logic=payload.logic)
    db.add(scale)
    db.flush()

    for item in payload.items:
        db.add(ScaleItem(scale_id=scale.id, prompt=item.prompt, field_type=item.field_type, options=item.options))

    db.commit()
    db.refresh(scale)
    return scale


@app.post("/department/patients", response_model=PatientOut)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.DEPARTMENT_ADMIN.value:
        raise HTTPException(status_code=403, detail="只有部门管理员可以创建病人")

    patient_user = User(
        username=f"patient_{payload.name}_{int(datetime.utcnow().timestamp())}",
        display_name=payload.name,
        role=Role.PATIENT.value,
        department_id=current_user.department_id,
    )
    db.add(patient_user)
    db.flush()

    patient = Patient(name=payload.name, department_id=current_user.department_id, user_id=patient_user.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@app.post("/department/assignments", response_model=AssignmentOut)
def assign_scale(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.DEPARTMENT_ADMIN.value:
        raise HTTPException(status_code=403, detail="只有部门管理员可以下放量表")

    patient = db.query(Patient).get(payload.patient_id)
    scale = db.query(Scale).get(payload.scale_id)

    if not patient or patient.department_id != current_user.department_id:
        raise HTTPException(status_code=404, detail="病人不存在或不在当前部门")
    if not scale:
        raise HTTPException(status_code=404, detail="量表不存在")

    assignment = ScaleAssignment(
        patient_id=payload.patient_id,
        scale_id=payload.scale_id,
        assigned_by=current_user.id,
        allow_patient_view=payload.allow_patient_view,
        report_header=payload.report_header,
        evaluation_date=payload.evaluation_date or datetime.utcnow(),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@app.patch("/department/assignments/{assignment_id}/report-settings", response_model=AssignmentOut)
def update_report_settings(
    assignment_id: int,
    payload: AssignmentReportSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.DEPARTMENT_ADMIN.value:
        raise HTTPException(status_code=403, detail="只有部门管理员可以修改报告配置")

    assignment = db.query(ScaleAssignment).get(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")
    if assignment.patient.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="无权修改其他部门的任务")

    if payload.allow_patient_view is not None:
        assignment.allow_patient_view = payload.allow_patient_view
    if payload.report_header is not None:
        assignment.report_header = payload.report_header

    db.commit()
    db.refresh(assignment)
    return assignment


@app.get("/patient/assignments", response_model=List[AssignmentDetail])
def list_patient_assignments(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.PATIENT.value:
        raise HTTPException(status_code=403, detail="仅病人可以查看自己的任务")

    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="未找到病人资料")

    assignments = (
        db.query(ScaleAssignment)
        .filter(ScaleAssignment.patient_id == patient.id)
        .order_by(ScaleAssignment.evaluation_date.desc())
        .all()
    )
    details: List[AssignmentDetail] = []
    for assignment in assignments:
        details.append(
            AssignmentDetail(
                **AssignmentOut.model_validate(assignment).model_dump(),
                scale=ScaleOut.model_validate(assignment.scale),
                responses=[
                    {"item_id": r.item_id, "answer_text": r.answer_text}
                    for r in assignment.responses
                ],
            )
        )
    return details


@app.post("/patient/assignments/{assignment_id}/responses", response_model=AssignmentOut)
def submit_responses(
    assignment_id: int,
    submission: ResponseSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.PATIENT.value:
        raise HTTPException(status_code=403, detail="仅病人可以提交测评")

    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    assignment = db.query(ScaleAssignment).get(assignment_id)

    if not assignment or assignment.patient_id != patient.id:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.query(ScaleResponse).filter(ScaleResponse.assignment_id == assignment_id).delete()
    for response in submission.responses:
        db.add(
            ScaleResponse(
                assignment_id=assignment_id,
                item_id=response.item_id,
                answer_text=response.answer_text,
            )
        )

    assignment.completed_at = datetime.utcnow()
    assignment.duration_seconds = submission.duration_seconds
    db.commit()
    db.refresh(assignment)
    return assignment


@app.post("/bootstrap/super-admin", response_model=UserOut)
def bootstrap_super_admin(db: Session = Depends(get_db)):
    """Convenience route to create an initial超级管理员."""
    existing = db.query(User).filter(User.role == Role.SUPER_ADMIN.value).first()
    if existing:
        return existing

    user = User(username="superadmin", display_name="超级管理员", role=Role.SUPER_ADMIN.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
