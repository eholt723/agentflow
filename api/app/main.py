from fastapi import FastAPI
from pydantic import BaseModel
from app.clients.inference_client import run_inference

app = FastAPI(title="AgentFlow Decision Intelligence API")


class AnalyzeRequest(BaseModel):
    raw_notes: str
    criteria: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    system_prompt = """
You are a structured Decision Intelligence Agent.

Your job is to convert unstructured evaluation notes into a professional,
evidence-based decision memo.

Return output in clear sections:

1. Executive Summary
2. Strengths
3. Risks / Concerns
4. Missing Information
5. Recommendation
6. Confidence (Low / Medium / High)

Be concise, professional, and objective.
"""

    user_prompt = f"""
Raw Notes:
{request.raw_notes}

Evaluation Criteria:
{request.criteria or "None provided"}
"""

    try:
        llm_output = await run_inference(system_prompt, user_prompt)

        return {
            "memo": llm_output
        }

    except Exception as e:
        return {
            "error": "Inference service unavailable",
            "details": str(e)
        }
