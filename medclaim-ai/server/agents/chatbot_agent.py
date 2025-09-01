# server/agents/chatbot_agent.py
from typing import Optional, Dict, Any
from server.utils.gemini_client import call_gemini
from google.adk.tools import FunctionTool
from server.orchestrator.adk_workflow import ADKDocumentPipeline
from pathlib import Path
import json

# Expose pipeline-run as a tool so the chatbot can call it
async def run_pipeline_tool(file_path: str, policy_clauses: Optional[str] = "") -> Dict[str, Any]:
    pipeline = ADKDocumentPipeline(output_dir="uploads/markdown")
    return await pipeline.run(file_path, policy_clauses or "")

run_pipeline_tool_ft = FunctionTool(func=run_pipeline_tool)

class ChatbotAgent:
    """
    Light wrapper that can:
      - answer free-form questions via Gemini
      - call run_pipeline_tool to process a file when requested
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model

    async def respond(self, user_input: str, call_pipeline: bool = False, file_path: Optional[str] = None,
                      policy_clauses: Optional[str] = None) -> Dict[str, Any]:
        """
        If call_pipeline=True and file_path provided, run pipeline and incorporate result into response.
        Otherwise, answer directly using Gemini.
        Returns dict { "reply": str, "pipeline_result": optional }
        """
        if call_pipeline and file_path:
            pipeline_result = await run_pipeline_tool(file_path, policy_clauses or "")
            # create a short reply summarising pipeline result using Gemini or the summarizer tool
            summary = pipeline_result.get("summary") or pipeline_result.get("policy_decision") or {}
            # Ask Gemini to make a short reply
            prompt = f"User asked: {user_input}\nUse this pipeline summary to reply:\n{json.dumps(summary)}\nReply in 2 sentences."
            resp = await call_gemini(prompt, model=self.model, max_tokens=256)
            return {"reply": resp["text"], "pipeline_result": pipeline_result}
        else:
            # simple chat
            prompt = f"User: {user_input}\nRespond helpfully and concisely."
            resp = await call_gemini(prompt, model=self.model, max_tokens=256)
            return {"reply": resp["text"]}
