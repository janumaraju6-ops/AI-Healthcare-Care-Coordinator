from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.tools.notification_tool import NotificationTool
from datetime import datetime, timedelta
from fastapi import FastAPI

scheduler = AsyncIOScheduler()
notification_tool = NotificationTool()


def appointment_reminder_job() -> None:
    notification_tool.send_notification(
        title='Upcoming appointment reminder',
        message='You have an upcoming appointment scheduled soon. Please review your plan.',
    )


def medication_reminder_job() -> None:
    notification_tool.send_notification(
        title='Medication reminder',
        message='Please remember to take your scheduled medication on time today.',
    )


def start_scheduler(app: FastAPI) -> None:
    scheduler.add_job(appointment_reminder_job, 'interval', hours=24, id='appointment_reminder')
    scheduler.add_job(medication_reminder_job, 'interval', hours=12, id='medication_reminder')
    scheduler.start()
    app.state.scheduler = scheduler
