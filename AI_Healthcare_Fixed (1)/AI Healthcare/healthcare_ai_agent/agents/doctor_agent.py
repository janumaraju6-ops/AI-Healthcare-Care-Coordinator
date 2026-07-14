from services.tools.patient_tool import PatientTool
from services.tools.doctor_tool import DoctorTool
from services.ai_client import AIClient

DOMAIN_PROMPT = (
    "You are the Doctor Assistant specialist inside a multi-agent "
    "healthcare assistant. You focus on patient history, doctor profiles "
    "and specialties, visit summaries, and medical reports."
)


class DoctorAssistantAgent:
    def __init__(self) -> None:
        self.patient_tool = PatientTool()
        self.doctor_tool = DoctorTool()
        self.ai_client = AIClient()

    def handle(self, message: str, user: object, memory_text: str) -> str:
        lowered = message.lower()

        if 'history' in lowered or 'patient history' in lowered:
            raw_result = self.patient_tool.patient_history(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'summary' in lowered or 'visit notes' in lowered:
            raw_result = self.doctor_tool.doctor_profile(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'report' in lowered or 'medical report' in lowered:
            raw_result = self.doctor_tool.generate_report(message, user)
            return self._explain_action(message, raw_result, memory_text)

        return self._general_answer(message, memory_text)

    def _explain_action(self, message: str, raw_result: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            "A backend lookup related to the patient or doctor record has "
            f"just been completed. Backend result (ground truth, do not "
            f"contradict or invent additional facts beyond it): "
            f"\"{raw_result}\"\n\n"
            f"Patient's original message: \"{message}\"\n\n"
            "Write a warm, clear, detailed reply presenting this "
            "information, using only the facts in the backend result. Then "
            "add relevant general context or next steps the patient may "
            "find useful."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)

    def _general_answer(self, message: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            f"Patient's message: \"{message}\"\n\n"
            "Give a detailed, helpful answer. If relevant, mention that you "
            "can also pull up patient history, summarize a doctor's "
            "profile, or generate a medical report on request."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)