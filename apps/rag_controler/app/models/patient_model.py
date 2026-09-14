import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mrn = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    dob = Column(Date, nullable=True)
    sex = Column(String(20), nullable=True)
    status = Column(String(30), nullable=False, default="active")  # active / discharged
    department_id = Column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    department = relationship("Department", back_populates="patients")
    statuses = relationship(
        "PatientStatus",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(PatientStatus.recorded_at)",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PatientStatus(Base):
    __tablename__ = "patient_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient = relationship("Patient", back_populates="statuses")

    recorded_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    acuity_level = Column(String(50), nullable=False, default="Stable")
    raw_note = Column(Text, nullable=False)

    # Universal Vitals
    blood_pressure = Column(String(20), nullable=True)
    heart_rate = Column(Integer, nullable=True)
    temperature_c = Column(Float, nullable=True)

    # Dynamic Department Data
    department_data = Column(JSONB, nullable=False, server_default="{}")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
