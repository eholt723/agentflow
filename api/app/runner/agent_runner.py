from typing import Dict, Any


async def run_agent(message: str) -> Dict[str, Any]:
    """
    Placeholder for LangGraph orchestration.
    Will later call tools + inference.
    """

    # Temporary logic
    anomaly = "anomaly" in message.lower()

    return {
        "response": f"Agent processed: {message}",
        "anomaly_detected": anomaly,
        "actions_taken": []
    }
