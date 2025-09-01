from string import Template
import json 
from server.utils.gemini_client import call_gemini, safe_parse_json
POLICY_PROMPT = Template("""
You are a claims policy assistant. Given JSON extracted from a medical bill and the user's policy clauses,
return strict JSON containing:
{
  "eligible": true|false,
  "deductible_to_apply": number,
  "coinsurance": number,
  "copay": number,
  "allowed_amount": number,
  "notes": "string"
}
Be concise and return valid JSON only.
Extracted: $extracted
PolicyClauses: $clauses
""")
def extract_policy_clauses(policy_path: str) -> str:
    """
    Reads a policy PDF/DOCX and returns key clauses as plain text.
    """
    md_path = convert_pdf_to_markdown(policy_path)  # reuse your pdf_agent
    with open(md_path, "r") as f:
        text = f.read()
    # Optionally, summarize or extract relevant sections with Gemini
    return text

async def reason_policy_tool(extracted_json: dict[str, any], policy_clauses: str) -> dict[str, any]:
    extracted_str = json.dumps(extracted_json)
    prompt = POLICY_PROMPT.substitute(
        extracted=extracted_str,
        clauses=policy_clauses[:10000]
    )
    resp = await call_gemini(prompt)
    parsed = safe_parse_json(resp["text"])
    if parsed is None:
        return {"error": "policy_reasoner_failed", "raw": resp["text"]}
    return parsed
