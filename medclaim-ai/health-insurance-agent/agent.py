# health_insurance_agent/agents.py
from google.adk.agents import Agent
from google.adk.tools import agent_tool
from .tools import (
    policy_lookup_func_tool,
    coverage_calculator_func_tool,
    ocr_func_tool,
    eligibility_func_tool,
    form_generation_func_tool,
    insurance_api_func_tool,
    claim_status_func_tool
)
from .instructions import (
    policy_guidance_instruction,
    document_analyzer_instruction,
    coverage_eligibility_instruction,
    claim_processor_instruction,
    system_coordinator_instruction
)

# Policy Guidance Chatbot Agent
policy_guidance_agent = Agent(
    name="policy_guidance_chatbot",
    model="gemini-2.0-flash",
    instruction=policy_guidance_instruction,
    tools=[policy_lookup_func_tool, coverage_calculator_func_tool, claim_status_func_tool]
)

# Medical Document Analyzer Agent
document_analyzer_agent = Agent(
    name="medical_document_analyzer",
    model="gemini-2.0-flash",
    instruction=document_analyzer_instruction,
    tools=[ocr_func_tool, eligibility_func_tool]
)

# Claim Form Processor Agent
claim_processor_agent = Agent(
    name="claim_form_processor",
    model="gemini-2.0-flash",
    instruction=claim_processor_instruction,
    tools=[form_generation_func_tool, insurance_api_func_tool]
)

# Coverage Eligibility Validator Agent
coverage_eligibility_agent = Agent(
    name="coverage_eligibility_validator",
    model="gemini-2.0-flash",
    instruction=coverage_eligibility_instruction,
    tools=[eligibility_func_tool, coverage_calculator_func_tool]
)

# System Coordinator Agent (Orchestrator)
root_agent = Agent(
    name="system_coordinator",
    model="gemini-2.0-flash",
    instruction=system_coordinator_instruction,
    tools=[
        agent_tool.AgentTool(agent=policy_guidance_agent),
        agent_tool.AgentTool(agent=document_analyzer_agent),
        agent_tool.AgentTool(agent=claim_processor_agent),
        agent_tool.AgentTool(agent=coverage_eligibility_agent)
    ]
)
