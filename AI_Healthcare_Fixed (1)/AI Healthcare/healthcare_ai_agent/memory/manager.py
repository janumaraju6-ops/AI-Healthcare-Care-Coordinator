import json
from pathlib import Path
from typing import Dict, List


class MemoryManager:
    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or Path(__file__).resolve().parent / 'conversation_memory.json')
        self.user_memory: Dict[str, Dict[str, List[str]]] = self._load_storage()

    def _load_storage(self) -> Dict[str, Dict[str, List[str]]]:
        if not self.storage_path.exists():
            return {}
        try:
            with self.storage_path.open('r', encoding='utf-8') as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return {key: {subkey: list(values) for subkey, values in value.items()} for key, value in data.items()}
        except (json.JSONDecodeError, OSError):
            return {}
        return {}

    def _save_storage(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open('w', encoding='utf-8') as handle:
            json.dump(self.user_memory, handle, indent=2)

    def load_memory(self, user_id: str) -> Dict[str, List[str]]:
        if user_id not in self.user_memory:
            self.user_memory[user_id] = {
                'conversation_history': [],
                'patient_history': [],
                'doctor_history': [],
                'appointment_history': [],
                'treatment_history': [],
                'medication_history': [],
            }
            self._save_storage()
        return self.user_memory[user_id]

    def append_memory(self, user_id: str, category: str, message: str) -> None:
        memory = self.load_memory(user_id)
        if category not in memory:
            memory[category] = []
        memory[category].append(message)
        self._save_storage()

    def get_summary(self, user_id: str) -> str:
        memory = self.load_memory(user_id)
        sections = []
        for key, values in memory.items():
            if values:
                sections.append(f'{key.replace("_", " ").title()}: ' + ' | '.join(values[-5:]))
        return '\n'.join(sections)

    def get_history(self, user_id: str, limit: int = 20) -> List[str]:
        memory = self.load_memory(user_id)
        return memory.get('conversation_history', [])[-limit:]


memory_manager = MemoryManager()
