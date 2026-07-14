from services.tools.medication_tool import MedicationTool
from services.ai_client import AIClient

DOMAIN_PROMPT = (
    "You are the Medication Reminder specialist inside a multi-agent "
    "healthcare assistant. You focus on medication reminders, dosage "
    "schedules, adherence tracking, drug information, and side effects."
)


class MedicationReminderAgent:
    def __init__(self) -> None:
        self.tool = MedicationTool()
        self.ai_client = AIClient()

    def handle(self, message: str, user: object, memory_text: str) -> str:
        lowered = message.lower()

        if 'remind' in lowered or 'reminder' in lowered:
            raw_result = self.tool.create_reminder(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'update reminder' in lowered or 'edit reminder' in lowered:
            raw_result = self.tool.update_reminder(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'delete reminder' in lowered or 'cancel reminder' in lowered:
            raw_result = self.tool.delete_reminder(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'schedule' in lowered or 'medicine schedule' in lowered:
            raw_result = self.tool.medicine_schedule(message, user)
            return self._explain_action(message, raw_result, memory_text)

        return self._general_answer(message, memory_text)

    def _explain_action(self, message: str, raw_result: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            "A backend action on the patient's medication record has just "
            f"been completed. Backend result (ground truth, do not "
            f"contradict or invent additional facts beyond it): "
            f"\"{raw_result}\"\n\n"
            f"Patient's original message: \"{message}\"\n\n"
            "Write a warm, clear, detailed reply confirming what happened, "
            "using only the facts in the backend result. Then add relevant "
            "general medication guidance (e.g. adherence tips, common side "
            "effects to watch for) the patient may find useful, and remind "
            "them to confirm dosing details with their prescribing doctor."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)

    def _general_answer(self, message: str, memory_text: str) -> str:
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            f"Patient's message: \"{message}\"\n\n"
            "Give a detailed, helpful answer covering the relevant "
            "medication information. If relevant, mention that you can also "
            "set up a medication reminder, update or cancel an existing "
            "reminder, or list their current medicine schedule on request."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)