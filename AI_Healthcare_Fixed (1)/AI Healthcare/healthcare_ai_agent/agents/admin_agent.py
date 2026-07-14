from services.tools.patient_tool import PatientTool
from services.tools.doctor_tool import DoctorTool
from services.tools.appointment_tool import AppointmentTool
from services.ai_client import AIClient

DOMAIN_PROMPT = (
    "You are the Administrative specialist inside a multi-agent healthcare "
    "assistant. You focus on registering patients and doctors, searching "
    "records, and reporting/analytics for healthcare administration."
)


class AdministrativeAgent:
    def __init__(self) -> None:
        self.patient_tool = PatientTool()
        self.doctor_tool = DoctorTool()
        self.appointment_tool = AppointmentTool()
        self.ai_client = AIClient()

    def handle(self, message: str, user: object, memory_text: str) -> str:
        lowered = message.lower()

        if 'register patient' in lowered or 'create patient' in lowered:
            raw_result = self.patient_tool.add_patient(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'register doctor' in lowered or 'create doctor' in lowered:
            raw_result = self.doctor_tool.add_doctor(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'search patient' in lowered:
            raw_result = self.patient_tool.search_patient(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'search doctor' in lowered:
            raw_result = self.doctor_tool.search_doctor(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'analytics' in lowered or 'report' in lowered:
            raw_result = self.appointment_tool.analytics_report(message, user)
            return self._explain_action(message, raw_result, memory_text)

        return self._general_answer(message, memory_text)

    def _explain_action(self, message: str, raw_result: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            "A backend administrative action has just been completed. "
            f"Backend result (ground truth, do not contradict or invent "
            f"additional facts beyond it): \"{raw_result}\"\n\n"
            f"User's original message: \"{message}\"\n\n"
            "Write a clear, professional, detailed reply confirming what "
            "happened, using only the facts in the backend result, and add "
            "any relevant next-step guidance for healthcare administration."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)

    def _general_answer(self, message: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            f"User's message: \"{message}\"\n\n"
            "Give a detailed, helpful answer about healthcare "
            "administration. If relevant, mention that you can also "
            "register a patient or doctor, search records, or generate an "
            "analytics report on request."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)