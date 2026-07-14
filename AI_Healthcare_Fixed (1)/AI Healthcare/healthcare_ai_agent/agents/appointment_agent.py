from datetime import datetime
from services.tools.appointment_tool import AppointmentTool
from services.ai_client import AIClient
from memory.manager import memory_manager

DOMAIN_PROMPT = (
    "You are the Appointment specialist inside a multi-agent healthcare "
    "assistant. You focus on booking, cancelling, and rescheduling "
    "appointments, and checking doctor availability."
)


class AppointmentAgent:
    def __init__(self) -> None:
        self.tool = AppointmentTool()
        self.ai_client = AIClient()

    def handle(self, message: str, user: object, memory_text: str) -> str:
        lowered = message.lower()

        if 'book' in lowered or 'schedule' in lowered:
            raw_result = self.tool.book_appointment(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'cancel' in lowered:
            raw_result = self.tool.cancel_appointment(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'reschedule' in lowered or 'move' in lowered:
            raw_result = self.tool.reschedule_appointment(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'availability' in lowered or 'available' in lowered:
            raw_result = self.tool.doctor_availability(message, user)
            return self._explain_action(message, raw_result, memory_text)

        return self._general_answer(message, memory_text)

    def _explain_action(self, message: str, raw_result: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            "A backend action on the patient's appointment has just been "
            f"completed. Backend result (ground truth, do not contradict or "
            f"invent additional facts beyond it): \"{raw_result}\"\n\n"
            f"Patient's original message: \"{message}\"\n\n"
            "Write a warm, clear, detailed reply confirming what happened, "
            "using only the facts in the backend result. Then add any "
            "relevant, general preparation tips or next steps for the "
            "appointment."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)

    def _general_answer(self, message: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            f"Patient's message: \"{message}\"\n\n"
            "Give a detailed, helpful answer. If relevant, mention that you "
            "can also book, cancel, or reschedule an appointment, or check "
            "doctor availability on request."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)