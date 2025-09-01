# server/orchestrator/adk_workflow.py
from pathlib import Path
from typing import Dict, Any
from server.agents.pdf_agent import pdf_to_md_tool
from server.agents.extraction_agent import extract_fields_tool
from server.agents.policy_agent import reason_policy_tool
from server.agents.summarizer_agent import summarize_tool

# ADK pipeline runner (deterministic steps)
class ADKDocumentPipeline:
    def __init__(self, output_dir: str = "uploads/markdown"):
        self.output_dir = output_dir

    async def run(self, pdf_path: str, policy_clauses: str = "") -> Dict[str, Any]:
        # 1) convert pdf to md (pdf_to_md_tool is sync function, decorated as FunctionTool)
        md_result = pdf_to_md_tool(pdf_path, self.output_dir)
        md_path = md_result.get("md_path")
        if not md_path:
            raise RuntimeError("PDF conversion failed")

        # 2) extract fields
        extracted = await extract_fields_tool(md_path)

        # 3) policy reasoning
        policy_decision = await reason_policy_tool(extracted, policy_clauses)

        # 4) summarise
        summary = await summarize_tool(extracted, policy_decision)

        return {
            "extracted": extracted,
            "policy_decision": policy_decision,
            "summary": summary
        }
