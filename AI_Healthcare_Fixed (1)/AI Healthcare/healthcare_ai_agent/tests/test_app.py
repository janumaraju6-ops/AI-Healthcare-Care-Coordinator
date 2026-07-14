import pytest
from fastapi.testclient import TestClient
from app import app
from config import Settings
from agents.coordinator import CoordinatorAgent
from services.ai_client import AIClient

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'AI Healthcare Care Coordinator is running'}


def test_health_endpoint() -> None:
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_chat_endpoint_without_auth() -> None:
    response = client.post('/api/assistant/chat', json={'message': 'Help me book an appointment'})
    assert response.status_code == 200
    assert 'result' in response.json()


def test_general_questions_are_not_misclassified_as_appointments() -> None:
    coordinator = CoordinatorAgent()
    intent = coordinator.plan_intent('How can you help me with my healthcare today?')
    assert intent != 'appointment'


def test_general_fallback_response_is_conversational() -> None:
    client = AIClient()
    response = client._fallback_response('How can you help me with my healthcare today?')
    assert 'appointment' not in response.lower()
    assert 'help' in response.lower() or 'health' in response.lower()


def test_settings_use_fallback_secret_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('SECRET_KEY', raising=False)
    settings = Settings(_env_file=None)
    assert settings.SECRET_KEY == 'dev-secret-key-change-me'
