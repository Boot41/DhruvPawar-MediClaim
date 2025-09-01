# server/agents/pdf_agent.py
from pathlib import Path
from typing import Dict, Any
from google.adk.tools import FunctionTool
#from server.tools.pdf_utils import convert_pdf_to_markdown
from server.tools.pdf_utils import pdf_to_markdown_file as convert_pdf_to_markdown

# Deterministic utility wrapper. ADK will auto-wrap functions, but FunctionTool gives explicit naming.
def pdf_to_md_tool(pdf_path: str, output_dir: str = "uploads/markdown") -> Dict[str, Any]:
    """
    Convert a PDF file to markdown, return dict: {"md_path": str}
    pdf_path: str path to pdf
    output_dir: directory where md will be saved
    """
    pdf_p = Path(pdf_path)
    out_dir = Path(output_dir)
    md_path = convert_pdf_to_markdown(pdf_p, out_dir)
    return {"md_path": str(md_path)}

# Expose as FunctionTool (ADK will accept plain function too)
pdf_agent_tool = FunctionTool(func=pdf_to_md_tool)