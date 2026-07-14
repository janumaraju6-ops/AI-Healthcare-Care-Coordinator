from database.session import SessionLocal
from models.models import Patient


class PatientTool:
    def add_patient(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = Patient(
                first_name=user.full_name.split(' ')[0] if user.full_name else 'Patient',
                last_name=' '.join(user.full_name.split(' ')[1:]) if user.full_name and len(user.full_name.split(' ')) > 1 else 'Unknown',
                email=user.email,
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            return f'Patient record created for {patient.first_name} {patient.last_name}. ID: {patient.id}'

    def update_patient(self, message: str, user: object) -> str:
        return 'Patient update function is available. Please specify the fields and patient details.'

    def search_patient(self, message: str, user: object) -> str:
        term = message.split('search patient')[-1].strip()
        with SessionLocal() as db:
            patients = db.query(Patient).filter(Patient.first_name.ilike(f'%{term}%') | Patient.last_name.ilike(f'%{term}%')).all()
            return f'Found {len(patients)} patients matching "{term}".'

    def patient_history(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'Patient record not available.'
            return f'Patient {patient.first_name} {patient.last_name} has {len(patient.appointments)} appointments and {len(patient.treatments)} treatments on file.'
