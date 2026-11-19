import uuid
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base(metadata=MetaData(schema="clinical"))


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    patients = relationship("Patient", back_populates="department")


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


# ----------------------------------------------------------------- conversation ----
Base_conv = declarative_base(metadata=MetaData(schema="clinical_conversations"))


class User(Base_conv):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name = Column(String(64), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        String(20), nullable=False, default="physician"
    )  # physician / staff / admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base_conv):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(120))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    __table_args__ = (Index("ix_conversations_user_updated", "user_id", "updated_at"),)


class Message(Base_conv):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(16), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
