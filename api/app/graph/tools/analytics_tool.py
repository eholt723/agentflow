def run_analytics_query(date: str) -> dict:
    return {
        "metric": "daily_revenue",
        "value": 8200,
        "previous_average": 12000,
        "delta_percent": -31.6,
        "anomaly": True,
    }
