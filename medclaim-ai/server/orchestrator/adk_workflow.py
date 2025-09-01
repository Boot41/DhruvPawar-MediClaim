# server/orchestrator/adk_workflow.py
from pathlib import Path
from typing import Dict, Any
from server.agents.pdf_agent import pdf_to_md_tool
from server.agents.extraction_agent import extract_fields_tool
from server.agents.policy_agent import reason_policy_tool, extract_policy_clauses
from server.agents.summarizer_agent import summarize_tool

class ADKDocumentPipeline:
    """
    Full document pipeline for medical claims:
    1) Convert bill PDF to markdown
    2) Extract structured fields
    3) Extract policy clauses from policy PDF
    4) Determine coverage & eligibility
    5) Summarize results
    """

    def __init__(self, output_dir: str = "uploads/markdown"):
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    async def run(self, bill_pdf_path: str, policy_pdf_path: str) -> Dict[str, Any]:
        # --- 1) Convert bill PDF to Markdown ---
        md_result = pdf_to_md_tool(bill_pdf_path, self.output_dir)
        md_path = md_result.get("md_path")
        if not md_path:
            raise RuntimeError("PDF conversion failed for bill")

        # --- 2) Extract fields from bill ---
        extracted = await extract_fields_tool(md_path)

        # --- 3) Extract policy clauses ---
        policy_text = extract_policy_clauses(policy_pdf_path)

        # --- 4) Policy reasoning ---
        policy_decision = await reason_policy_tool(extracted, policy_text)

        # Optional: calculate out-of-pocket if allowed_amount > 0
        deductible = policy_decision.get("deductible_to_apply", 0)
        coinsurance = policy_decision.get("coinsurance", 0)
        allowed_amount = policy_decision.get("allowed_amount", 0)

        out_of_pocket = deductible + coinsurance * max(0, allowed_amount - deductible)
        policy_decision["out_of_pocket_estimate"] = round(out_of_pocket, 2)

        # --- 5) Summarize ---
        summary = await summarize_tool(extracted, policy_decision)

        return {
            "extracted": extracted,
            "policy_decision": policy_decision,
            "summary": summary
        }
