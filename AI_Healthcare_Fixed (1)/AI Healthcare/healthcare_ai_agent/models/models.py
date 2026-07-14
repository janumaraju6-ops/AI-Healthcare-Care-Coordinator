from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database.session import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(256), nullable=True)
    role = Column(String(32), default='patient')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patients = relationship('Patient', back_populates='user')


class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False)
    phone = Column(String(64), nullable=True)
    dob = Column(String(32), nullable=True)
    gender = Column(String(32), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(256), nullable=True)
    medical_conditions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='patients')
    appointments = relationship('Appointment', back_populates='patient')
    treatments = relationship('Treatment', back_populates='patient')
    medicines = relationship('Medicine', back_populates='patient')
    histories = relationship('MedicalHistory', back_populates='patient')
    notifications = relationship('Notification', back_populates='patient')


class Doctor(Base):
    __tablename__ = 'doctors'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False)
    phone = Column(String(64), nullable=True)
    specialty = Column(String(128), nullable=True)
    department = Column(String(128), nullable=True)
    availability = Column(Text, nullable=True)
    profile = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship('Appointment', back_populates='doctor')
    treatments = relationship('Treatment', back_populates='doctor')
    notifications = relationship('Notification', back_populates='doctor')


class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(64), default='scheduled')
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship('Patient', back_populates='appointments')
    doctor = relationship('Doctor', back_populates='appointments')


class Treatment(Base):
    __tablename__ = 'treatments'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    plan = Column(Text, nullable=False)
    progress_notes = Column(Text, nullable=True)
    status = Column(String(64), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship('Patient', back_populates='treatments')
    doctor = relationship('Doctor', back_populates='treatments')


class Medicine(Base):
    __tablename__ = 'medicines'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    name = Column(String(256), nullable=False)
    dosage = Column(String(128), nullable=True)
    frequency = Column(String(128), nullable=True)
    instructions = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    adherence_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship('Patient', back_populates='medicines')


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=True)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(64), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(64), default='pending')

    patient = relationship('Patient', back_populates='notifications')
    doctor = relationship('Doctor', back_populates='notifications')


class MedicalHistory(Base):
    __tablename__ = 'medical_history'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    record_date = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text, nullable=False)
    details = Column(Text, nullable=True)

    patient = relationship('Patient', back_populates='histories')


class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    report_type = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmergencyContact(Base):
    __tablename__ = 'emergency_contacts'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    phone = Column(String(64), nullable=False)
    relationship = Column(String(128), nullable=True)
    hospital_name = Column(String(256), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
