from google.adk.agents import Agent
from .tools import (
    policy_lookup_tool,
    coverage_calculator_tool,
    check_claim_eligibility,
    generate_claim_estimate,
    get_claim_status
)

root_agent = Agent(
    name="health_insurance_claim_assistant",
    model="gemini-2.0-flash",
    description=(
        "A helpful health insurance claim assistant that helps policyholders "
        "understand their coverage, calculate claim amounts, analyze medical bills, "
        "and guide them through the claims process."
    ),
    instruction=(
        "You are a knowledgeable and empathetic health insurance assistant. "
        "Help policyholders with:\n"
        "1. Understanding their policy coverage and benefits\n"
        "2. Calculating out-of-pocket costs and insurance coverage\n"
        "3. Analyzing medical bills and determining eligibility\n"
        "4. Explaining the claims process step-by-step\n"
        "5. Checking claim status and tracking submissions\n\n"
        
        "Always be clear, patient, and supportive. If you need the user's "
        "policy number to help them, ask for it politely. Explain complex "
        "insurance terms in simple language."
    ),
    tools=[
        policy_lookup_tool,
        coverage_calculator_tool,
        check_claim_eligibility,
        generate_claim_estimate,
        get_claim_status
    ]
)
