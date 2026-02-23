# schemas/tools/analytics.py
from pydantic import BaseModel


class AnalyticsQueryInput(BaseModel):
    date: str  # ISO format: YYYY-MM-DD


class AnalyticsQueryResult(BaseModel):
    metric: str
    value: float
    previous_average: float
    delta_percent: float
    anomaly: bool
