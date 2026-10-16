import json
import os
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from models import Base, Department, Patient, PatientStatus

engine = create_engine(os.environ["ADMIN_DATABASE_URL"])


def init_schema():
    with engine.begin() as conn:
        conn.execute(text("create schema if not exists clinical"))
    Base.metadata.create_all(engine)


def make_mrn(rec: dict) -> str:
    # avoid duplicates
    key = f"{rec['name']}|{rec['dob']}"
    return "MRN-" + uuid.uuid5(uuid.NAMESPACE_DNS, key).hex[:8].upper()


def seed():
    records = json.loads((Path(__file__).parent / "data" / "patients.json").read_text())
    with Session(engine) as s:
        for rec in records:
            mrn = rec.get("mrn") or make_mrn(rec)
            if s.scalar(select(Patient).where(Patient.mrn == mrn)):
                continue  # already seeded

            dept = s.scalar(
                select(Department).where(Department.name == rec["department"])
            )
            if dept is None:
                dept = Department(name=rec["department"])
                s.add(dept)
                s.flush()

            s.add(
                Patient(
                    mrn=mrn,
                    name=rec["name"],
                    dob=date.fromisoformat(rec["dob"]),
                    sex=rec.get("sex"),
                    department=dept,
                    statuses=[
                        PatientStatus(
                            raw_note=rec["raw_note"],
                            acuity_level=rec.get("acuity_level", "Stable"),
                            blood_pressure=rec.get("blood_pressure"),
                            heart_rate=rec.get("heart_rate"),
                            temperature_c=rec.get("temperature_c"),
                            department_data=rec.get("department_data", {}),
                        )
                    ],
                )
            )
        s.commit()


if __name__ == "__main__":
    init_schema()
    seed()
    print("done")
