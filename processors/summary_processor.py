from typing import List, Dict
from models.account import Account
from .openai_adapter import call_openai_api
import json
import re

def generate_summary_data(
    accounts: List[Account], 
    inquiries: List[Dict], 
    credit_repair_items: List[Dict], 
    report_summary: Dict
) -> Dict:
    """
    Calculates pay-off amounts and generates a qualitative summary using an LLM.
    """
    # Ensure report_summary is a dictionary
    if not isinstance(report_summary, dict):
        report_summary = {}
        
    # 1. Calculate Pay-off amounts
    payoff_summary = {
        "Total to Reach 'A' Rating": 0,
        "Total to Reach 'B' Rating": 0,
        "Total to Reach 'C' Rating": 0,
    }
    for acc in accounts:
        if acc.balance > 0 and acc.limit > 0:
            if acc.rating != 'A' and acc.a_rating_limit is not None:
                payoff_summary["Total to Reach 'A' Rating"] += acc.balance - acc.a_rating_limit
            if acc.rating not in ['A', 'B'] and acc.b_rating_limit is not None:
                payoff_summary["Total to Reach 'B' Rating"] += acc.balance - acc.b_rating_limit
            if acc.rating not in ['A', 'B', 'C'] and acc.c_rating_limit is not None:
                payoff_summary["Total to Reach 'C' Rating"] += acc.balance - acc.c_rating_limit

    # Clean up negative values (if already better than target)
    for key in payoff_summary:
        if payoff_summary[key] < 0:
            payoff_summary[key] = 0

    # 2. Get AI-powered credit potential analysis
    system_prompt = (
        "You are a professional financial analyst. Based on the client's structured credit data, you will produce a funding potential assessment. "
        "Your entire response MUST be a single, valid JSON object with three keys: 'risk_bracket' (string), 'analysis_explanation' (string), and 'charge_off_red_flag' (boolean). "
        "The 'risk_bracket' should be one of the specified funding tiers. The 'analysis_explanation' should be a paragraph justifying your decision based on the rules."

        "\n\n--- Underwriting Rules ---"
        "\n\n**Funding Tiers (Base Assessment):**"
        "\n1. **$50,000 - $100,000:** Client must have 5-7 accounts, a diversified debt history, AND 7+ years average age of accounts."
        "\n2. **$35,000 - $50,000:** Client must have 5-7 accounts OR 5+ years of history."
        "\n3. **$15,000 - $35,000:** Client must have 3-4 accounts OR 2-4 years of history."
        "\n4. **$0 - $15,000:** Client has 0-2 individually held accounts OR 0-2 years average age of accounts."
        
        "\n\n**Negative Factors (Knock-Downs):**"
        "\n- If any derogatory marks or closed revolving accounts with balances are present, move the client DOWN one funding bracket."
        "\n- If there are more than 3 inquiries on any single credit bureau, also move the client DOWN one funding bracket."

        "\n\n**Red Flags (Immediate Action Required):**"
        "\n1. **Bankruptcies:** If present, the 'risk_bracket' is capped at **$28,000** MAXIMUM."
        "\n2. **Excessive Charge-offs:** Set 'charge_off_red_flag' to true if the client has charge-offs with more than three of the following 'big banks': Citibank, Bank of America, Capital One, Chase, American Express, US Bank, Barclays, Discover."
        
        "\n\n--- Instructions ---"
        "\n- Start with the highest bracket the client qualifies for and apply knock-downs."
        "\- Provide your final assessment as a JSON object only. Do not include markdown or any other commentary."
    )
    
    accounts_summary_for_prompt = [acc.to_dict() for acc in accounts]

    user_prompt = (
        "Here is the client's credit data. Provide your funding potential assessment as a JSON object according to the strict underwriting guidelines.\n"
        f"- Raw Report Summary Data: {json.dumps(report_summary)}\n"
        f"- Processed Accounts: {json.dumps(accounts_summary_for_prompt)}\n"
        f"- Inquiries: {json.dumps(inquiries)}\n"
        f"- Credit Repair Items (Derogatories): {json.dumps(credit_repair_items)}\n"
    )
    
    ai_analysis_json = {
        "risk_bracket": "Error",
        "analysis_explanation": "Could not generate AI analysis due to an API or parsing error.",
        "charge_off_red_flag": False
    }

    response = call_openai_api(system_prompt, user_prompt)
    if response:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            # Find the JSON object within the response
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                ai_analysis_json = json.loads(match.group(0))
            else:
                print("Warning: Could not find a JSON object in the AI response.")
        except json.JSONDecodeError:
            print(f"Warning: Failed to decode JSON from AI response. Content: {content}")

    # Combine all data into the final summary dictionary
    final_summary_data = {
        "payoff_summary": payoff_summary,
        "ai_analysis": ai_analysis_json,
        "counts": {
            "Accounts": len(accounts),
            "Inquiries": len(inquiries),
            "Credit Repair Items": len(credit_repair_items)
        }
    }
    return final_summary_data 