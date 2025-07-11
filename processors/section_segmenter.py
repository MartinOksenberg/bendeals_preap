import json
from dotenv import load_dotenv
from .openai_adapter import call_openai_api
import re

load_dotenv()

def segment_credit_report(text, max_retries=2):
    """
    Use an LLM to extract relevant sections from a single credit report chunk in a stateless manner.
    Includes a retry mechanism for JSON parsing failures.
    Args:
        text: The chunk of credit report text to analyze.
    Returns:
        A dictionary with extracted data from the chunk, or None on failure.
    """
    system_prompt = (
        "You are an expert at reading US credit reports. You will be given a chunk of a credit report. "
        "Your entire response must be a single, valid JSON object. "
        "Your job is to extract any relevant information from THIS CHUNK ONLY. "
        "The output JSON object must have these four top-level keys: "
        "1. 'report_summary': A dictionary of high-level stats (FICO Score, Total Debt, etc.). ONLY populate this if you see a summary section in the text. If not found, return an empty dictionary {}. "
        "2. 'surviving_inquiries': A list of all inquiries found in this chunk (e.g., [{date, creditor, type}, ...]). If none are found, you MUST return an empty list []. "
        "3. 'accounts': a list of ALL accounts found in this chunk, including credit cards, charge accounts, revolving, installment, and mortgages. For each, extract relevant info (bank, type, open_date, balance, limit, responsibility, etc). If none are found, you MUST return an empty list []. "
        "4. 'credit_repair': A list of JSON objects for negative items with keys: 'BUREAU', 'TYPE', 'Account', 'Occurrence', 'LAST DLQ', 'NOTES', 'INITIAL'. Only include genuinely negative items like late payments or collections. If none are found, you MUST return an empty list []."
        "IMPORTANT: Adhere strictly to the JSON format. If a key finds no data, return the specified empty type (e.g., [] or {}). "
        "Return ONLY the JSON object. Do not include any explanation, commentary, or markdown code fences."
    )

    user_prompt = f"Credit Report Chunk:\n{text}"

    for attempt in range(max_retries + 1):
        try:
            response_data = call_openai_api(system_prompt, user_prompt)
            if not response_data:
                print("API call failed, continuing to next attempt.")
                continue

            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                print("No content in API response, continuing to next attempt.")
                continue
            
            # The most reliable way to extract JSON is to find the first '{' and last '}'
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                json_string = match.group(0)
                return json.loads(json_string)
            else:
                print(f"Attempt {attempt + 1}: No JSON object found in response. Retrying...")
                continue
        
        except json.JSONDecodeError:
            if attempt < max_retries:
                print(f"Attempt {attempt + 1}: Failed to parse JSON. Retrying...")
                continue
            else:
                print("Failed to parse JSON on final attempt.")
                # Log the problematic content for debugging
                print("--- Problematic AI Response ---")
                print(content)
                print("-----------------------------")
                return None # Return None on final failure
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break # Exit loop on other errors

    return None

