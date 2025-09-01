# server/agents/extraction_agent.py
from pathlib import Path
from typing import Dict, Any
from google.adk.tools import FunctionTool
from server.tools.text_utils import read_and_clean_text
from server.utils.gemini_client import call_gemini, safe_parse_json

# Prompt template - keep concise and instruct strict JSON output
EXTRACT_PROMPT = """
You are a strict JSON extractor for medical/insurance documents.
Given the markdown content, return only valid JSON matching this schema:
{{
  "patient": {{"name": null, "dob": null, "member_id": null}},
  "provider": {{"name": null, "npi": null, "address": null}},
  "dates": {{"service_date": null}},
  "line_items": [{{"description": null, "code": null, "amount": null}}],
  "totals": {{"total": null}},
  "confidence": null
}}
Document:
{document_text}
"""


async def extract_fields_tool(md_path: str) -> Dict[str, Any]:
    """
    Reads markdown file, calls Gemini to extract fields as strict JSON.
    Returns parsed JSON dict or a fallback wrapper with raw LLM text.
    """
    md_file = Path(md_path)
    text = read_and_clean_text(md_file)
    prompt = EXTRACT_PROMPT.format(document_text=text[:15000])  # truncate if necessary
    response = await call_gemini(prompt)
    parsed = safe_parse_json(response["text"])
    if parsed is None:
        # fallback: return raw LLM text with low confidence
        return {"raw_text": response["text"], "confidence": 0.0}
    return parsed

extraction_agent_tool = FunctionTool(func=extract_fields_tool)