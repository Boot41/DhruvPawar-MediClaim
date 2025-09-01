# agents/verification_agent.py
class VerificationAgent:
    async def verify(self, extracted_data: dict) -> dict:
        # Optional: verify consistency, confidence checks
        extracted_data["verified"] = True
        return extracted_data
