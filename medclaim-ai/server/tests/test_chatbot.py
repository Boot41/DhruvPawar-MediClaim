import asyncio
from server.agents.chatbot_agent import ChatbotAgent

async def main():
    chatbot = ChatbotAgent()
    result = await chatbot.respond(
        user_input="Please process my medical bill.",
        call_pipeline=True,
        file_path="uploads/bills/sample_bill.pdf",
        policy_clauses="Policy covers 80% after $500 deductible."
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
