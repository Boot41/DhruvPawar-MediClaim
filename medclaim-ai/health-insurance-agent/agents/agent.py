# health_insurance_agent/agents.py
from google.adk.agents import Agent
from google.adk.tools import agent_tool
from agents.tools import (
    policy_extract_func_tool,
    invoice_extract_func_tool,
    ocr_func_tool,
    coverage_calc_func_tool,
)
from agents.claim_agent_tools import (
    get_popular_vendors_tool,
    vendor_search_func_tool,
)
from agents.instructions import (
    policy_guidance_instruction,
    document_analyzer_instruction,
    coverage_eligibility_instruction,
    claim_processor_instruction,
    form_automation_instruction,
    system_coordinator_instruction
)
from agents.form_automation_tools import (
    test_pdf_download_func_tool,
    fill_local_pdf_func_tool,
    identify_missing_fields_func_tool,
    generate_missing_data_prompt_func_tool,
    retrieve_pdf_func_tool,
    map_data_to_fields_func_tool,
    extract_form_fields_func_tool
)
# 1. Policy Guidance Agent
policy_guidance_agent = Agent(
    name="policy_guidance_agent",
    model="gemini-2.5-flash",
    instruction=policy_guidance_instruction,
    tools=[policy_extract_func_tool, coverage_calc_func_tool]
)

# 2. Medical Document Analyzer Agent
document_analyzer_agent = Agent(
    name="medical_document_analyzer",
    model="gemini-2.5-flash",
    instruction=document_analyzer_instruction,
    tools=[ocr_func_tool, invoice_extract_func_tool]
)

# 3. Coverage Eligibility Agent
coverage_eligibility_agent = Agent(
    name="coverage_eligibility_agent",
    model="gemini-2.5-flash",
    instruction=coverage_eligibility_instruction,
    tools=[policy_extract_func_tool, coverage_calc_func_tool]
)

# 4. Claim Form Processor Agent
claim_processor_agent = Agent(
    name="claim_form_processor",
    model="gemini-2.5-flash",
    instruction=claim_processor_instruction,
    tools=[fill_local_pdf_func_tool,
    test_pdf_download_func_tool,
    vendor_search_func_tool,
    ocr_func_tool,
    invoice_extract_func_tool,
    policy_extract_func_tool,
    get_popular_vendors_tool]
)
# 4. Form Automation Agent
form_automation_agent = Agent(
    name="form_automation_agent",
    model="gemini-2.5-flash",
    instruction=form_automation_instruction,
    tools=[retrieve_pdf_func_tool,
    test_pdf_download_func_tool,
    fill_local_pdf_func_tool,
    identify_missing_fields_func_tool,
    generate_missing_data_prompt_func_tool,
    extract_form_fields_func_tool,
    map_data_to_fields_func_tool]
)
# 5. System Coordinator Agent (Orchestrator)
root_agent = Agent(
    name="system_coordinator",
    model="gemini-2.5-flash",
    instruction=system_coordinator_instruction,
    tools=[
        agent_tool.AgentTool(agent=policy_guidance_agent),
        agent_tool.AgentTool(agent=document_analyzer_agent),
        agent_tool.AgentTool(agent=coverage_eligibility_agent),
        agent_tool.AgentTool(agent=claim_processor_agent),
        agent_tool.AgentTool(agent=form_automation_agent)
    ]
)
