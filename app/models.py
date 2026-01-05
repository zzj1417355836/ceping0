from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    DEPARTMENT_ADMIN = "department_admin"
    PATIENT = "patient"


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    admins = relationship("User", back_populates="department")
    patients = relationship("Patient", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    department = relationship("Department", back_populates="admins")
    patient = relationship("Patient", uselist=False, back_populates="user")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    department = relationship("Department", back_populates="patients")
    user = relationship("User", back_populates="patient")
    assignments = relationship("ScaleAssignment", back_populates="patient")


class Scale(Base):
    __tablename__ = "scales"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    logic = Column(Text, nullable=True)

    items = relationship("ScaleItem", back_populates="scale", cascade="all, delete-orphan")


class ScaleItem(Base):
    __tablename__ = "scale_items"

    id = Column(Integer, primary_key=True, index=True)
    scale_id = Column(Integer, ForeignKey("scales.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    field_type = Column(String, nullable=False, default="single_choice")
    options = Column(Text, nullable=True)

    scale = relationship("Scale", back_populates="items")


class ScaleAssignment(Base):
    __tablename__ = "scale_assignments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    scale_id = Column(Integer, ForeignKey("scales.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    allow_patient_view = Column(Boolean, default=False)
    report_header = Column(String, nullable=True)
    evaluation_date = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    patient = relationship("Patient", back_populates="assignments")
    scale = relationship("Scale")
    responses = relationship("ScaleResponse", back_populates="assignment", cascade="all, delete-orphan")


class ScaleResponse(Base):
    __tablename__ = "scale_responses"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("scale_assignments.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("scale_items.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("ScaleAssignment", back_populates="responses")
    item = relationship("ScaleItem")
