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

# Policy Guidance Chatbot Agent
policy_guidance_agent = Agent(
    name="policy_guidance_chatbot",
    model="gemini-2.0-flash",
    instruction="""You are a helpful health insurance chatbot. Answer user questions about policies, calculate claim eligibility, and guide them with empathy.""",
    tools=[policy_lookup_func_tool, coverage_calculator_func_tool, claim_status_func_tool]
)

# Medical Document Analyzer Agent
document_analyzer_agent = Agent(
    name="medical_document_analyzer",
    model="gemini-2.0-flash",
    instruction="""Extract and validate information from medical bills and documents, using OCR and eligibility tools.""",
    tools=[ocr_func_tool, eligibility_func_tool]
)

# Claim Form Processor Agent
claim_processor_agent = Agent(
    name="claim_form_processor",
    model="gemini-2.0-flash",
    instruction="""Auto-generate and submit claim forms; validate all data before submission.""",
    tools=[form_generation_func_tool, insurance_api_func_tool]
)

# Coverage Eligibility Validator Agent
coverage_eligibility_agent = Agent(
    name="coverage_eligibility_validator",
    model="gemini-2.0-flash",
    instruction="""Check policy coverage, validate eligibility, and calculate claim amounts.""",
    tools=[eligibility_func_tool, coverage_calculator_func_tool]
)

# System Coordinator Agent (Orchestrator)
root_agent = Agent(
    name="system_coordinator",
    model="gemini-2.0-flash",
    instruction="""
    You are the orchestrator for the Health Insurance Claim Assistant.
    Route requests to the appropriate specialized agent:
      - Chatbot: policy questions
      - Document Analyzer: uploads
      - Claim Processor: new claims
      - Coverage Validator: eligibility and calculations
    Aggregate multi-step workflows for the user.
    """,
    tools=[
        agent_tool.AgentTool(agent=policy_guidance_agent),
        agent_tool.AgentTool(agent=document_analyzer_agent),
        agent_tool.AgentTool(agent=claim_processor_agent),
        agent_tool.AgentTool(agent=coverage_eligibility_agent)
    ]
)
