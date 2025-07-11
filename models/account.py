from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Account:
    """A structured data class for a credit account."""
    bank: str
    account_type: str
    open_date: str
    balance: float
    limit: float
    status: str
    responsibility: Optional[str] = None
    monthly_payment: Optional[float] = None
    highest_balance: Optional[float] = None
    utilization: Optional[float] = None
    rating: Optional[str] = None
    a_rating_limit: Optional[float] = None
    b_rating_limit: Optional[float] = None
    c_rating_limit: Optional[float] = None

    def __post_init__(self):
        """Perform post-initialization data cleaning and calculations."""
        # Clean up balance and limit fields
        if isinstance(self.balance, str):
            self.balance = float(self.balance.replace('$', '').replace(',', ''))
        if isinstance(self.limit, str):
            self.limit = float(self.limit.replace('$', '').replace(',', ''))
        
        # Calculate utilization and ratings
        if self.limit and self.limit > 0:
            self.utilization = round(self.balance / self.limit, 2)
            self.assign_rating()
            self.calculate_rating_limits()

    def assign_rating(self, thresholds: List[float] = [0.1, 0.2, 0.3]):
        """Assign an A, B, C rating based on utilization."""
        if self.utilization is None:
            return

        if self.utilization <= thresholds[0]:
            self.rating = 'A'
        elif self.utilization <= thresholds[1]:
            self.rating = 'B'
        elif self.utilization <= thresholds[2]:
            self.rating = 'C'
        else:
            self.rating = 'D'

    def calculate_rating_limits(self, thresholds: List[float] = [0.1, 0.2, 0.3]):
        """Calculate the balance required for A, B, C ratings."""
        if self.limit and self.limit > 0:
            self.a_rating_limit = self.limit * thresholds[0]
            self.b_rating_limit = self.limit * thresholds[1]
            self.c_rating_limit = self.limit * thresholds[2]

    def to_dict(self):
        """Convert the account object to a dictionary."""
        return {
            "Bank": self.bank,
            "Account Type": self.account_type,
            "Open Date": self.open_date,
            "Responsibility": self.responsibility,
            "Balance": self.balance,
            "Limit": self.limit,
            "Utilization": f"{self.utilization:.0%}" if self.utilization is not None else "N/A",
            "Rating": self.rating,
            "A Rating Limit (10%)": self.a_rating_limit,
            "B Rating Limit (20%)": self.b_rating_limit,
            "C Rating Limit (30%)": self.c_rating_limit,
            "Status": self.status,
        } 