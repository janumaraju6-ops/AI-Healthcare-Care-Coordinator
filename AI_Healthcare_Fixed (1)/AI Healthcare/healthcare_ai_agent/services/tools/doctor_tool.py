from database.session import SessionLocal
from models.models import Doctor


class DoctorTool:
    def add_doctor(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            doctor = Doctor(
                first_name='Doctor',
                last_name='Assistant',
                email='doctor@example.com',
                specialty='General Medicine',
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            return f'Doctor record created for {doctor.first_name} {doctor.last_name}. ID: {doctor.id}'

    def doctor_schedule(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            doctor = db.query(Doctor).first()
            if not doctor:
                return 'No doctor schedule is available at the moment.'
            return f'Dr. {doctor.first_name} {doctor.last_name} is available for appointments. Specialty: {doctor.specialty}.'

    def doctor_profile(self, message: str, user: object) -> str:
        doctor = self.doctor_schedule(message, user)
        return doctor

    def search_doctor(self, message: str, user: object) -> str:
        term = message.split('search doctor')[-1].strip()
        with SessionLocal() as db:
            doctors = db.query(Doctor).filter(Doctor.first_name.ilike(f'%{term}%') | Doctor.last_name.ilike(f'%{term}%')).all()
            return f'Found {len(doctors)} doctors matching "{term}".'

    def generate_report(self, message: str, user: object) -> str:
        return 'Doctor report generation is available. Please specify the patient or date range.'

    def handle_general(self, message: str, user: object) -> str:
        return 'I can retrieve patient history, create visit notes, and support doctor workflows.'
