# routers/patients_admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.department_model import Department
from app.models.patient_model import Patient
from app.schemas.patient_schemas import PatientCreate, PatientOut

router = APIRouter(prefix="/patients", tags=["patients"])

"""Exp sync data
{
  "name": "Helen Tran",
  "dob": "1994-03-12",
  "sex": "female",
  "department": "Obstetrics",
  "raw_note": "32-year-old G2P1 at 28 weeks gestation, referred for elevated glucose on routine screening. 1-hour 50g glucose challenge test: 168 mg/dL (positive, threshold 140). Confirmatory 3-hour 100g OGTT: fasting 98 mg/dL, 1hr 195 mg/dL, 2hr 172 mg/dL, 3hr 145 mg/dL — meets criteria for gestational diabetes mellitus (Carpenter-Coustan). Pre-pregnancy BMI 31 (obese class I). No personal history of diabetes; family history of T2DM in mother. Current medications: prenatal vitamin, folic acid 800mcg daily. No known drug allergies. Blood pressure stable at 118/76, no proteinuria on urinalysis. Patient reports mild fatigue, no visual disturbances or headaches. Fetal growth on last ultrasound (26 weeks) tracking at 78th percentile, amniotic fluid index normal. Patient counseled on initial management with dietary modification and glucose self-monitoring 4x daily; referred to nutrition for medical nutrition therapy. Plan to reassess in 1-2 weeks and consider pharmacologic therapy (metformin vs insulin) if glycemic targets not met with lifestyle changes alone."
}
"""

@router.post("/", response_model=PatientOut)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    department = None
    if payload.department:
        department = db.query(Department).filter(Department.name == payload.department).first()
        if not department:
            department = Department(name=payload.department)
            db.add(department)
            db.flush()

    patient = Patient(
        name=payload.name,
        dob=payload.dob,
        sex=payload.sex,
        raw_note=payload.raw_note,
        department_id=department.id if department else None,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@router.get("/", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: str, payload: PatientCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in payload.model_dump().items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient

@router.delete("/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return None
    db.delete(patient)
    db.commit()
    return {"message": f"Patient {patient.id} deleted successfully"}