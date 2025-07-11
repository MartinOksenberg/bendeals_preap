from typing import List, Dict, Union
from models.account import Account

def _parse_float(value: Union[str, int, float]) -> float:
    """Safely parse a value to a float, returning 0.0 on failure."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            # Remove common non-numeric characters and convert
            cleaned_value = value.replace('$', '').replace(',', '').strip()
            return float(cleaned_value)
        except (ValueError, TypeError):
            # Return 0.0 if the string is "N/A", "Not Reported", or anything else non-numeric
            return 0.0
    return 0.0

def process_accounts(accounts_data: List[Dict]) -> List[Account]:
    """
    Process raw account data into a list of Account objects.
    """
    processed_accounts = []
    for acc_data in accounts_data:
        try:
            account = Account(
                bank=acc_data.get("bank", "N/A"),
                account_type=acc_data.get("type", "N/A"),
                open_date=acc_data.get("open_date", "N/A"),
                balance=_parse_float(acc_data.get("balance", "0")),
                limit=_parse_float(acc_data.get("limit", "0")),
                status=acc_data.get("status", "N/A"),
                responsibility=acc_data.get("responsibility", "N/A"),
            )
            processed_accounts.append(account)
        except (ValueError, TypeError) as e:
            print(f"Skipping account due to unexpected data error: {acc_data}. Error: {e}")
            continue
    return processed_accounts 