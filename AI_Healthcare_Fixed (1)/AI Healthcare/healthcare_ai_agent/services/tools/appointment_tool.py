from datetime import datetime, timedelta
from database.session import SessionLocal
from models.models import Appointment, Doctor, Patient
from typing import Optional


class AppointmentTool:
    def __init__(self) -> None:
        pass

    def _extract_datetime(self, message: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(message.strip())
        except ValueError:
            return None

    def book_appointment(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            doctor = db.query(Doctor).first()
            if not patient or not doctor:
                return 'Could not find a valid patient or doctor for booking.'
            scheduled_time = datetime.utcnow() + timedelta(days=1)
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scheduled_time=scheduled_time,
                reason='Appointment requested by patient',
            )
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            return f'Appointment booked with Dr. {doctor.first_name} {doctor.last_name} for {scheduled_time.isoformat()}.'

    def cancel_appointment(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'Could not find a patient record to cancel an appointment for.'
            appointment = db.query(Appointment).filter(Appointment.patient_id == patient.id, Appointment.status == 'scheduled').order_by(Appointment.scheduled_time.desc()).first()
            if not appointment:
                return 'No scheduled appointment found to cancel.'
            appointment.status = 'cancelled'
            db.commit()
            return 'The appointment has been cancelled successfully.'

    def reschedule_appointment(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.email == user.email).first()
            if not patient:
                return 'Could not find a patient record to reschedule an appointment for.'
            appointment = db.query(Appointment).filter(Appointment.patient_id == patient.id, Appointment.status == 'scheduled').first()
            if not appointment:
                return 'No appointment found to reschedule.'
            appointment.scheduled_time = datetime.utcnow() + timedelta(days=2)
            db.commit()
            return f'Appointment has been rescheduled to {appointment.scheduled_time.isoformat()}.'

    def doctor_availability(self, message: str, user: object) -> str:
        with SessionLocal() as db:
            doctor = db.query(Doctor).first()
            if not doctor:
                return 'No doctor availability information is available at this time.'
            return f'Dr. {doctor.first_name} {doctor.last_name} is currently available. Specialty: {doctor.specialty}.'

    def handle_general(self, message: str, user: object) -> str:
        return 'I can help with appointment booking, cancellations, rescheduling, and availability checks.'

    def analytics_report(self, message: str, user: object) -> str:
        return 'Appointment analytics are under development. I can summarize trends, doctor workload, and follow-up schedules.'
