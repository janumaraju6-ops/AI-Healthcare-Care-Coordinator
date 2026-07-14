class EmergencySupportAgent:
    def detect_emergency(self, message: str) -> bool:
        lower = message.lower()
        return any(term in lower for term in ['emergency', 'urgent', 'help now', 'pain', 'bleeding', 'collapse'])

    def handle(self, message: str) -> str:
        return (
            'I am here to help. If this is an emergency, please contact your local emergency services immediately. '
            'I can also provide nearby hospital contact information if you share your location. Always consult licensed healthcare professionals for urgent medical attention.'
        )
