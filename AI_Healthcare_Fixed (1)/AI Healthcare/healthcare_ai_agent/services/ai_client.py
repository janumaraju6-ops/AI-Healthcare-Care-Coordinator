import logging
import os
import time
from typing import Generator, Optional

from dotenv import load_dotenv

from config import settings

load_dotenv()

logger = logging.getLogger("healthcare_ai_agent.ai_client")

# This system instruction is prepended to every user-facing generation so the
# model consistently behaves as a healthcare-only assistant, regardless of
# what the user asks. Internal, non-user-facing calls (e.g. intent
# classification) skip this via `apply_persona=False`.
HEALTHCARE_SYSTEM_PROMPT = (
    "You are the AI Healthcare Care Coordinator, a specialized healthcare "
    "assistant. You help with: symptoms, diseases, medications, dosage "
    "guidance, side effects, treatments, medical terminology, appointment "
    "scheduling, doctor recommendations, preventive care, lifestyle "
    "guidance, and general health education. "
    "You are not a replacement for a licensed medical professional, and for "
    "anything urgent you should tell the user to seek emergency care. "
    "If the user's message is NOT related to healthcare, medicine, or "
    "wellbeing in any way, do NOT answer the off-topic question. Instead, "
    "politely explain that you specialize in healthcare topics and ask them "
    "to rephrase with a healthcare-related question. "
    "Format your answers using clear, readable Markdown (short paragraphs, "
    "bullet points for lists, and bold for key terms) and keep them concise "
    "and easy to scan. Write the Markdown directly as your reply -- do NOT "
    "wrap your entire response in a code block or triple backticks (```); "
    "only use a code block for literal code snippets, if any."
)


class AIClient:
    """Thin wrapper around Google Gemini (via LangChain, with a raw
    google-generativeai fallback) that provides both a normal
    request/response call and a token-streaming call, plus a deterministic
    offline fallback so the app keeps working even if the Gemini API key is
    missing or the API call fails.
    """

    def __init__(self) -> None:
        self.llm = None
        self.generative_model = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning(
                "GOOGLE_API_KEY is not configured. The assistant will use the "
                "offline fallback responder until a valid key is provided in .env"
            )
            return

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL_NAME,
                google_api_key=api_key,
                temperature=0.2,
            )
            logger.info("Gemini model '%s' initialized via LangChain.", settings.GEMINI_MODEL_NAME)
            return
        except Exception:
            logger.exception("Failed to initialize ChatGoogleGenerativeAI, trying raw google-generativeai SDK.")
            self.llm = None

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self.generative_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
            logger.info("Gemini model '%s' initialized via google-generativeai SDK.", settings.GEMINI_MODEL_NAME)
        except Exception:
            logger.exception("Failed to initialize google-generativeai SDK. Falling back to offline responses.")
            self.generative_model = None

    def get_llm(self):
        return self.llm or self.generative_model

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """Defensive cleanup: some models wrap an entire Markdown reply in a
        ``` code fence (sometimes with a language tag like ```markdown)
        instead of just writing Markdown directly, which makes chat UIs
        render the whole answer as an unformatted, non-wrapping code block.
        This strips a fence that wraps the *whole* response, without
        touching legitimate code blocks embedded partway through a reply.
        """
        stripped = text.strip()
        if stripped.startswith("```") and stripped.endswith("```") and stripped.count("```") == 2:
            inner = stripped[3:-3].strip()
            # Drop a leading language tag on its own first line, e.g. "markdown\n..."
            first_line, _, rest = inner.partition("\n")
            if rest and first_line.strip().isalpha():
                return rest.strip()
            return inner
        return text

    @staticmethod
    def _extract_text(content) -> str:
        """Normalizes a LangChain message `.content` value into plain text.

        Newer langchain-google-genai versions can return `.content` as a
        list of content blocks (e.g. [{"type": "text", "text": "..."}])
        instead of a plain string, depending on the response shape. This
        flattens either form into a single string so downstream code
        (e.g. coordinator.py calling `.strip()`) never breaks.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict):
                    text = block.get("text") or block.get("content") or ""
                    if text:
                        parts.append(str(text))
            return "".join(parts)
        return str(content)

    def _build_prompt(self, prompt: str, context: Optional[str], apply_persona: bool) -> str:
        parts = []
        if apply_persona:
            parts.append(HEALTHCARE_SYSTEM_PROMPT)
        if context:
            parts.append(f"Conversation memory so far:\n{context}")
        parts.append(f"User message:\n{prompt}")
        return "\n\n".join(parts)

    def generate_response(self, prompt: str, context: Optional[str] = None, apply_persona: bool = True) -> str:
        """Generates a single, complete response (no streaming)."""
        full_prompt = self._build_prompt(prompt, context, apply_persona)

        if self.llm is not None:
            try:
                response = self.llm.invoke(full_prompt)
                return self._strip_code_fence(self._extract_text(getattr(response, "content", str(response))))
            except Exception:
                logger.exception("Gemini (LangChain) invocation failed, falling back.")

        if self.generative_model is not None:
            try:
                response = self.generative_model.generate_content(full_prompt)
                return self._strip_code_fence(getattr(response, "text", str(response)))
            except Exception:
                logger.exception("Gemini (google-generativeai) invocation failed, falling back.")

        return self._fallback_response(prompt, context)

    def generate_response_stream(
        self,
        prompt: str,
        context: Optional[str] = None,
        apply_persona: bool = True,
    ) -> Generator[str, None, None]:
        """Streams the response back chunk by chunk.

        Prefers a true token stream from Gemini via LangChain's `.stream()`.
        If that isn't available, simulates streaming by chunking a
        deterministic response so the frontend UX stays consistent either way.
        """
        full_prompt = self._build_prompt(prompt, context, apply_persona)

        if self.llm is not None:
            try:
                streamed_any = False
                for chunk in self.llm.stream(full_prompt):
                    raw_content = getattr(chunk, "content", None)
                    text = self._extract_text(raw_content) if raw_content else ""
                    if text:
                        streamed_any = True
                        yield text
                if streamed_any:
                    return
            except Exception:
                logger.exception("Gemini streaming (LangChain) failed, falling back to non-streaming call.")

        if self.generative_model is not None:
            try:
                response_stream = self.generative_model.generate_content(full_prompt, stream=True)
                streamed_any = False
                for chunk in response_stream:
                    text = getattr(chunk, "text", None)
                    if text:
                        streamed_any = True
                        yield text
                if streamed_any:
                    return
            except Exception:
                logger.exception("Gemini streaming (google-generativeai) failed, falling back to non-streaming call.")

        # Final fallback: simulate a natural typing effect over the
        # deterministic response so the UI still feels alive when Gemini is
        # unreachable.
        fallback_text = self._fallback_response(prompt, context)
        for word in fallback_text.split(" "):
            yield word + " "
            time.sleep(0.02)

    def _fallback_response(self, prompt: str, context: Optional[str] = None) -> str:
        lowered = prompt.lower()
        if 'emergency' in lowered or 'urgent' in lowered or 'pain' in lowered:
            return 'This may be urgent. Please contact emergency services immediately if you are in danger.'
        if 'medication' in lowered or 'medicine' in lowered or 'pill' in lowered or 'dose' in lowered:
            return 'I can help with medication questions and reminders. Please share the medication name and schedule.'
        if 'treatment' in lowered or 'therapy' in lowered or 'rehab' in lowered:
            return 'I can assist with treatment tracking and care questions. Please describe the treatment concern.'
        if 'doctor' in lowered or 'clinic' in lowered or 'specialist' in lowered:
            return 'I can help connect you with the right doctor or clinic. Please describe your need.'
        if 'admin' in lowered or 'record' in lowered or 'report' in lowered:
            return 'I can help with administrative requests and records. Please tell me what you need.'
        if 'appointment' in lowered or 'schedule' in lowered or 'book' in lowered or 'reschedule' in lowered:
            return 'I can help with appointment booking and scheduling. Please provide your preferred date and time.'
        if any(term in lowered for term in ['help', 'health', 'healthcare', 'support', 'care']):
            return 'I can help with your healthcare questions, medication guidance, treatment support, doctor questions, and general care support. Tell me what you need help with.'
        return 'I can help with your healthcare questions, medication guidance, treatment support, doctor questions, and general care support.'