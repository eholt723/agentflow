import os
import httpx

INFERENCE_BASE_URL = os.getenv("INFERENCE_BASE_URL", "http://localhost:8080")
MODEL_NAME = os.getenv("INFERENCE_MODEL_NAME", "local-model")


async def run_inference(system_prompt: str, user_prompt: str) -> str:
    url = f"{INFERENCE_BASE_URL}/v1/chat/completions"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"]
