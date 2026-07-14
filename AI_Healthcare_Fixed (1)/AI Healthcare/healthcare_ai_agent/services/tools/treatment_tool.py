from datetime import datetime
from database.session import SessionLocal
from models.models import Treatment, Patient


class TreatmentTool:
    def create_treatment(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'No patient record found to create treatment.'
            treatment = Treatment(
                patient_id=patient.id,
                doctor_id=1,
                start_date=datetime.utcnow(),
                plan='Standard care with daily monitoring',
            )
            db.add(treatment)
            db.commit()
            db.refresh(treatment)
            return f'Treatment plan created with ID {treatment.id}.'

    def update_treatment(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'No patient record found to update a treatment for.'
            treatment = db.query(Treatment).filter(Treatment.patient_id == patient.id, Treatment.status == 'active').order_by(Treatment.created_at.desc()).first()
            if not treatment:
                return 'No active treatment plan found to update.'
            treatment.progress_notes = 'Updated progress review.'
            db.commit()
            return 'Treatment progress notes updated.'

    def treatment_summary(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'No patient record found to summarize treatments for.'
            treatments = db.query(Treatment).filter(Treatment.patient_id == patient.id).all()
            return f'Patient has {len(treatments)} treatment records. Latest status: {treatments[-1].status if treatments else "none"}.'

    def handle_general(self, message: str, user: object) -> str:
        return 'I can help create treatment plans, track progress, and summarize therapy milestones.'
