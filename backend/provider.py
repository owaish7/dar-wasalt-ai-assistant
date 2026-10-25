"""Free-only OpenRouter adapter. Never log provider bodies or credentials."""
import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator

import httpx


class ProviderFailure(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class OpenRouter:
    def __init__(self, api_key: str, model: str, client: httpx.AsyncClient, fallback_models: tuple[str, ...] = ()):
        self.api_key, self.model, self.client = api_key, model, client
        self.candidates = tuple(dict.fromkeys((model, *fallback_models)))
        self.available_models = self.candidates
        self.checked_at: float | None = None

    async def check_model(self):
        if self.candidates == ("openrouter/free",):
            return
        if any(m != "openrouter/free" and not m.endswith(":free") for m in self.candidates):
            raise ProviderFailure("model_not_free", "Only free models are permitted.")
        if self.checked_at is not None and time.monotonic() - self.checked_at < 600:
            return
        response = await self.client.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        catalog = {m["id"]: m for m in response.json()["data"]}
        available = []
        for model in self.candidates:
            if model == "openrouter/free":
                available.append(model)
                continue
            entry = catalog.get(model)
            if entry is None:
                continue
            if any(float(entry["pricing"].get(k, "1")) != 0 for k in ("prompt", "completion")) or float(entry["pricing"].get("request", "0")) != 0:
                raise ProviderFailure("model_not_free", "A configured model has non-zero pricing.")
            available.append(model)
        if not available:
            raise ProviderFailure("model_not_free", "No configured free models are currently available.")
        self.available_models = tuple(available)
        self.checked_at = time.monotonic()

    async def rewrite(self, messages: list[dict]) -> AsyncIterator[dict]:
        async for part in self.stream(messages, prefer_fallback=True):
            yield part

    async def stream(self, messages: list[dict], prefer_fallback=False) -> AsyncIterator[dict]:
        if not self.api_key:
            raise ProviderFailure("not_configured", "The server needs an OpenRouter API key. No model response was generated.")
        await self.check_model()
        models = list(self.available_models)
        if prefer_fallback and len(models) > 1:
            models = models[1:] + models[:1]
        # Retry only a transient status before any generation starts, never a partial answer.
        for attempt in range(2):
            async with self.client.stream("POST", "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": "Bearer " + self.api_key},
                    json={"models": models, "messages": messages, "stream": True,
                          "max_tokens": 900, "temperature": 0.1,
                          "reasoning": {"effort": "none"}}) as response:
                if response.status_code in {429, 502, 503} and attempt == 0:
                    retry_after = response.headers.get("Retry-After", "1")
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        delay = 60
                    # A long quota cooldown is reported instead of tying up a worker.
                    if 0 <= delay <= 2:
                        await asyncio.sleep(delay)
                        continue
                if response.status_code != 200:
                    logging.getLogger("uvicorn.error").warning("openrouter_unavailable status=%s model=%s", response.status_code, self.model)
                    code = "quota" if response.status_code in {402, 429} else "provider_unavailable"
                    if response.status_code in {401, 403}:
                        code = "provider_auth"
                    raise ProviderFailure(code, "Free inference is unavailable or its quota was reached. Please try later.")
                completed = False
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        if not completed:
                            raise ProviderFailure("interrupted", "The provider ended before completing its answer.")
                        return
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise ProviderFailure("invalid_response", "The provider returned an invalid response.") from exc
                    if payload.get("error"):
                        raise ProviderFailure("interrupted", "The provider interrupted this answer. Please retry.")
                    if payload.get("model"):
                        yield {"model": payload["model"]}
                    for choice in payload.get("choices", []):
                        if choice.get("finish_reason") == "error":
                            raise ProviderFailure("interrupted", "The provider interrupted this answer.")
                        if choice.get("finish_reason") == "length":
                            raise ProviderFailure("truncated", "The answer exceeded its limit. Please ask a narrower question.")
                        if choice.get("finish_reason") == "stop":
                            completed = True
                        delta = choice.get("delta", {}).get("content")
                        if delta:
                            yield {"delta": delta}
                if completed:
                    return
                raise ProviderFailure("interrupted", "The connection closed before the answer completed.")
