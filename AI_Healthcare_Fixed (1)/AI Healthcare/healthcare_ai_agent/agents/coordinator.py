import logging
from typing import Any, Generator

from agents.admin_agent import AdministrativeAgent
from agents.appointment_agent import AppointmentAgent
from agents.doctor_agent import DoctorAssistantAgent
from agents.emergency_agent import EmergencySupportAgent
from agents.medication_agent import MedicationReminderAgent
from agents.treatment_agent import TreatmentMonitoringAgent
from memory.manager import memory_manager
from services.ai_client import AIClient

logger = logging.getLogger("healthcare_ai_agent.coordinator")

# Intents that are handled by deterministic, database-backed tools rather
# than by calling the LLM. Their responses are already guaranteed to be
# healthcare-related, so they don't need the off-topic gate applied.
TOOL_BACKED_INTENTS = {"appointment", "medication", "treatment", "doctor", "admin", "emergency"}


class CoordinatorAgent:
    def __init__(self) -> None:
        self.ai_client = AIClient()
        self.appointment_agent = AppointmentAgent()
        self.medication_agent = MedicationReminderAgent()
        self.treatment_agent = TreatmentMonitoringAgent()
        self.doctor_agent = DoctorAssistantAgent()
        self.admin_agent = AdministrativeAgent()
        self.emergency_agent = EmergencySupportAgent()

    # ------------------------------------------------------------------
    # Standard (non-streaming) entry point
    # ------------------------------------------------------------------
    def handle_request(self, message: str, user: Any) -> str:
        memory_text = memory_manager.get_summary(str(user.id))

        if self.emergency_agent.detect_emergency(message):
            response = self.emergency_agent.handle(message)
            self._remember_turn(user, message, response)
            return response

        intent = self.plan_intent(message)
        response = self.route_intent(intent, message, user, memory_text)
        self._remember_turn(user, message, response)
        return response

    # ------------------------------------------------------------------
    # Streaming entry point
    # ------------------------------------------------------------------
    def handle_request_stream(self, message: str, user: Any) -> Generator[str, None, None]:
        """Yields the assistant's reply incrementally.

        Tool-backed intents (appointments, medication, etc.) produce a
        complete deterministic string from the database, so it is streamed
        back word-by-word to keep a consistent "typing" UX. Free-form
        healthcare questions are streamed directly, token by token, from
        Gemini.
        """
        memory_text = memory_manager.get_summary(str(user.id))
        collected: list[str] = []

        if self.emergency_agent.detect_emergency(message):
            response = self.emergency_agent.handle(message)
            for chunk in self._simulate_stream(response):
                collected.append(chunk)
                yield chunk
            self._remember_turn(user, message, "".join(collected))
            return

        intent = self.plan_intent(message)

        if intent in TOOL_BACKED_INTENTS:
            response = self.route_intent(intent, message, user, memory_text)
            for chunk in self._simulate_stream(response):
                collected.append(chunk)
                yield chunk
        else:
            for chunk in self.ai_client.generate_response_stream(message, memory_text):
                collected.append(chunk)
                yield chunk

        self._remember_turn(user, message, "".join(collected))

    @staticmethod
    def _simulate_stream(text: str) -> Generator[str, None, None]:
        for word in text.split(" "):
            yield word + " "

    def _remember_turn(self, user: Any, user_message: str, assistant_response: str) -> None:
        """Persists both sides of the exchange so future turns have real
        conversational context (previously only the user's message was
        stored, which meant the assistant had no memory of its own replies).
        """
        user_id = str(user.id)
        memory_manager.append_memory(user_id, "conversation_history", f"User: {user_message}")
        memory_manager.append_memory(user_id, "conversation_history", f"Assistant: {assistant_response}")

    # ------------------------------------------------------------------
    # Intent planning / routing
    # ------------------------------------------------------------------
    def plan_intent(self, user_message: str) -> str:
        message = user_message.strip().lower()

        if any(term in message for term in ['emergency', 'urgent', 'pain', 'bleeding', 'collapse', 'help now']):
            return 'emergency'
        if any(term in message for term in ['medication', 'medicine', 'pill', 'dose', 'reminder', 'adherence']):
            return 'medication'
        if any(term in message for term in ['treatment', 'therapy', 'rehab', 'progress', 'plan']):
            return 'treatment'
        if any(term in message for term in ['doctor', 'clinic', 'specialist', 'doctor appointment', 'consult']):
            return 'doctor'
        if any(term in message for term in ['admin', 'register', 'report', 'analytics', 'patient record', 'doctor record']):
            return 'admin'
        if any(term in message for term in ['appointment', 'schedule', 'book', 'cancel', 'reschedule', 'availability', 'visit']):
            return 'appointment'
        if any(term in message for term in ['how can you help', 'what can you do', 'can you help', 'healthcare', 'health', 'support', 'information']):
            return 'unknown'

        prompt = (
            'Classify the following user request into one of these categories: appointment, medication, treatment, doctor, admin, emergency, analytics, unknown. '
            'Return only the category label.\nRequest: ' + user_message
        )
        # apply_persona=False: this is an internal classification call, not a
        # user-facing chat reply, so it should not be wrapped in the
        # healthcare persona / off-topic-refusal instructions.
        try:
            result = self.ai_client.generate_response(prompt, apply_persona=False)
        except Exception:
            logger.exception("Intent classification call failed; defaulting to 'unknown'.")
            return 'unknown'
        mapped = result.strip().lower()
        for option in ['appointment', 'medication', 'treatment', 'doctor', 'admin', 'emergency', 'analytics']:
            if option in mapped:
                return option
        return 'unknown'

    def route_intent(self, intent: str, message: str, user: Any, memory_text: str) -> str:
        if intent == 'appointment':
            return self.appointment_agent.handle(message, user, memory_text)
        if intent == 'medication':
            return self.medication_agent.handle(message, user, memory_text)
        if intent == 'treatment':
            return self.treatment_agent.handle(message, user, memory_text)
        if intent == 'doctor':
            return self.doctor_agent.handle(message, user, memory_text)
        if intent == 'admin':
            return self.admin_agent.handle(message, user, memory_text)
        if intent == 'emergency':
            return self.emergency_agent.handle(message)
        # 'unknown' / free-form: let Gemini answer directly. The
        # HEALTHCARE_SYSTEM_PROMPT (apply_persona=True, the default) ensures
        # off-topic questions are politely declined instead of answered.
        return self.ai_client.generate_response(message, memory_text)
