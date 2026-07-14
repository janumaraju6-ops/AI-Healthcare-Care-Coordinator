from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = 'patient'


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_conditions: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    specialty: Optional[str] = None
    department: Optional[str] = None
    availability: Optional[str] = None
    profile: Optional[str] = None


class DoctorCreate(DoctorBase):
    pass


class DoctorRead(DoctorBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    scheduled_time: datetime
    status: Optional[str] = 'scheduled'
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentRead(AppointmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TreatmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    plan: str
    progress_notes: Optional[str] = None
    status: Optional[str] = 'active'


class TreatmentCreate(TreatmentBase):
    pass


class TreatmentRead(TreatmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicineBase(BaseModel):
    patient_id: int
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    instructions: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    adherence_notes: Optional[str] = None


class MedicineCreate(MedicineBase):
    pass


class MedicineRead(MedicineBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationBase(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    title: str
    message: str
    notification_type: Optional[str] = None
    status: Optional[str] = 'pending'


class NotificationCreate(NotificationBase):
    pass


class NotificationRead(NotificationBase):
    id: int
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicalHistoryBase(BaseModel):
    patient_id: int
    summary: str
    details: Optional[str] = None


class MedicalHistoryCreate(MedicalHistoryBase):
    pass


class MedicalHistoryRead(MedicalHistoryBase):
    id: int
    record_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportBase(BaseModel):
    title: str
    content: str
    report_type: Optional[str] = None


class ReportRead(ReportBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
