import asyncio
from server.agents.chatbot_agent import ChatbotAgent

chatbot = ChatbotAgent()

async def main():
    while True:
        query = input("You: ")
        if query.lower() in ["exit", "quit"]:
            break
        response = await chatbot.respond(None, query)
        print("Bot:", response["reply"])

asyncio.run(main())
