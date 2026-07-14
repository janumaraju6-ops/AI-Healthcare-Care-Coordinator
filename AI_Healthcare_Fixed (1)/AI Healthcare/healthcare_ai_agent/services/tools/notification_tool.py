from smtplib import SMTP
from email.mime.text import MIMEText
from models.models import Notification
from database.session import SessionLocal
from config import settings


class NotificationTool:
    def send_email(self, recipient: str, subject: str, body: str) -> str:
        if not settings.EMAIL_SMTP_SERVER or not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
            return 'Email settings are not configured.'
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = settings.EMAIL_USERNAME
        msg['To'] = recipient
        try:
            with SMTP(settings.EMAIL_SMTP_SERVER, settings.EMAIL_SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                smtp.send_message(msg)
            return 'Email sent successfully.'
        except Exception as exc:
            return f'Failed to send email: {exc}'

    def send_sms(self, phone: str, message: str) -> str:
        return f'SMS dispatch simulated to {phone}. Message: {message}'

    def send_notification(self, title: str, message: str, patient_id: int | None = None, doctor_id: int | None = None) -> str:
        with SessionLocal() as db:
            notification = Notification(
                title=title,
                message=message,
                patient_id=patient_id,
                doctor_id=doctor_id,
                status='sent',
            )
            db.add(notification)
            db.commit()
            return 'Notification stored and delivered.'
