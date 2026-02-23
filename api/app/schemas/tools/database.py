# schemas/tools/database.py
from pydantic import BaseModel


class DatabaseLookupInput(BaseModel):
    date: str  # ISO format: YYYY-MM-DD


class DatabaseLookupResult(BaseModel):
    failed_transactions: int
    top_customer_segment: str
    region: str
