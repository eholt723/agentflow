import base64
import logging

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from api.app.settings import settings

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception(_is_retryable),
    reraise=True,
)
async def run_inference(system_prompt: str, user_prompt: str) -> str:
    url = f"{settings.groq_base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }

    logger.debug("inference request model=%s url=%s", settings.groq_model, url)

    async with httpx.AsyncClient(timeout=settings.inference_timeout_seconds) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    logger.debug("inference response tokens=%s", data.get("usage", {}).get("total_tokens"))
    return content


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception(_is_retryable),
    reraise=True,
)
async def run_vision_inference(prompt: str, image_bytes: bytes, media_type: str) -> str:
    """
    Send an image to Groq's vision model and return the text response.
    media_type should be e.g. 'image/jpeg', 'image/png', 'image/webp'.
    """
    url = f"{settings.groq_base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": settings.groq_vision_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}},
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    logger.debug("vision request model=%s media_type=%s bytes=%d",
                 settings.groq_vision_model, media_type, len(image_bytes))

    async with httpx.AsyncClient(timeout=settings.vision_timeout_seconds) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    logger.debug("vision response tokens=%s", data.get("usage", {}).get("total_tokens"))
    return content
