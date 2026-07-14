from database.session import SessionLocal
from models.models import Medicine, Patient
from datetime import datetime


class MedicationTool:
    def create_reminder(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'Could not find the patient record for medication reminders.'
            medicine = Medicine(
                patient_id=patient.id,
                name='Daily Medication',
                dosage='As prescribed',
                frequency='Daily',
                instructions='Take with water',
                start_date=datetime.utcnow(),
            )
            db.add(medicine)
            db.commit()
            db.refresh(medicine)
            return f'Medication reminder created for {medicine.name}.'

    def update_reminder(self, message: str, user: object) -> str:
        return 'Medication reminder update is ready. Please clarify which reminder you want to update.'

    def delete_reminder(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'Could not find a patient record to delete a reminder for.'
            medicine = db.query(Medicine).filter(Medicine.patient_id == patient.id).order_by(Medicine.created_at.desc()).first()
            if not medicine:
                return 'No reminders were found to delete.'
            db.delete(medicine)
            db.commit()
            return f'Reminder for {medicine.name} deleted.'

    def medicine_schedule(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'Cannot find the patient profile for schedule details.'
            medicines = db.query(Medicine).filter(Medicine.patient_id == patient.id).all()
            if not medicines:
                return 'No active medicine schedule found.'
            schedule = ', '.join([f'{m.name} ({m.frequency})' for m in medicines])
            return f'Active medication schedule: {schedule}.'

    def handle_general(self, message: str, user: object) -> str:
        return 'I can manage medication reminders, adherence tracking, and schedule summaries.'
