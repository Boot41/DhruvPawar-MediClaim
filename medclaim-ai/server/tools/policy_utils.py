def validate_claim(extracted_data: dict) -> dict:
    """
    Performs basic policy validation.
    Replace this with calls to policy database or rule engine.
    """
    policy_number = extracted_data.get("policy_number")
    claim_amount = extracted_data.get("bill_amount", 0)

    # Example policy rules
    valid_policies = {"P123456": 50000, "P789012": 100000}
    max_coverage = valid_policies.get(policy_number, 0)

    if max_coverage == 0:
        status = "Rejected"
        reason = "Invalid policy number"
    elif claim_amount > max_coverage:
        status = "Partial Approval"
        reason = f"Amount exceeds coverage limit of {max_coverage}"
    else:
        status = "Approved"
        reason = "Within coverage limits"

    return {
        "policy_number": policy_number,
        "claim_amount": claim_amount,
        "status": status,
        "reason": reason
    }
