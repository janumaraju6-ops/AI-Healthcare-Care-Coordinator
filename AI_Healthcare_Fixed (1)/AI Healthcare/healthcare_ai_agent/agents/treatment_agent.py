from services.tools.treatment_tool import TreatmentTool
from services.ai_client import AIClient

# System framing for this agent's Gemini calls. Kept separate from the
# global HEALTHCARE_SYSTEM_PROMPT in ai_client.py so the model additionally
# knows it is speaking specifically as the Treatment Monitoring specialist.
DOMAIN_PROMPT = (
    "You are the Treatment Monitoring specialist inside a multi-agent "
    "healthcare assistant. You focus on treatment plans, therapy progress, "
    "rehabilitation, and care-plan monitoring."
)


class TreatmentMonitoringAgent:
    def __init__(self) -> None:
        self.tool = TreatmentTool()
        self.ai_client = AIClient()

    def handle(self, message: str, user: object, memory_text: str) -> str:
        lowered = message.lower()

        if 'monitor' in lowered or 'progress' in lowered:
            raw_result = self.tool.treatment_summary(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'create treatment' in lowered or 'new treatment' in lowered:
            raw_result = self.tool.create_treatment(message, user)
            return self._explain_action(message, raw_result, memory_text)
        if 'update treatment' in lowered or 'edit treatment' in lowered:
            raw_result = self.tool.update_treatment(message, user)
            return self._explain_action(message, raw_result, memory_text)

        return self._general_answer(message, memory_text)

    def _explain_action(self, message: str, raw_result: str, memory_text: str) -> str:
        """Turns a raw, deterministic DB-tool result into a detailed,
        AI-generated explanation instead of returning the bare string."""
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            "A backend action on the patient's treatment record has just been "
            f"completed. Backend result (ground truth, do not contradict or "
            f"invent additional facts beyond it): \"{raw_result}\"\n\n"
            f"Patient's original message: \"{message}\"\n\n"
            "Write a warm, clear, detailed reply confirming what happened, "
            "using only the facts in the backend result. Then add relevant, "
            "general treatment or therapy guidance the patient may find useful."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)

    def _general_answer(self, message: str, memory_text: str) -> str:
        """No specific tool action matched -- answer like a knowledgeable
        assistant instead of a static placeholder string."""
        prompt = (
            f"{DOMAIN_PROMPT}\n\n"
            f"Patient's message: \"{message}\"\n\n"
            "Give a detailed, helpful answer. If relevant, mention that you "
            "can also create a new treatment plan, update an existing one, "
            "or summarize the patient's treatment progress on request."
        )
        return self.ai_client.generate_response(prompt, context=memory_text)