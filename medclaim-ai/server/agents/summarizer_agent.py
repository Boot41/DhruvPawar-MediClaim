# server/agents/summarizer_agent.py
from typing import Dict, Any
from google.adk.tools import FunctionTool
from server.utils.gemini_client import call_gemini
import json

SUMMARIZE_PROMPT = """
You are a customer-facing assistant. Given the extraction json and policy decision, generate:
1) a short plain-English summary (2-5 sentences)
2) a next-steps checklist for the user (bulleted)
Return JSON:
{{
  "summary": "...",
  "next_steps": ["...", "..."]
}}
Extracted: {extracted}
PolicyDecision: {decision}
"""

async def summarize_tool(extracted: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
    prompt = SUMMARIZE_PROMPT.format(extracted=json.dumps(extracted), decision=json.dumps(decision))
    resp = await call_gemini(prompt)
    parsed = None
    try:
        parsed = json.loads(resp["text"])
    except Exception:
        # If LLM returned plain text, ask it to produce JSON - but for now fallback to raw text
        return {"summary": resp["text"], "next_steps": []}
    return parsed

summarizer_agent_tool = FunctionTool(func=summarize_tool)