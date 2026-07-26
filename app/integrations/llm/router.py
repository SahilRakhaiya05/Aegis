"""Multi-provider LLM router for Aegis."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str


def resolve_backend() -> str:
    choice = (settings.LLM_BACKEND or "auto").strip().lower()
    if choice not in {"auto", "gemini", "openai", "ollama", "mock", "offline"}:
        choice = "auto"
    if choice in {"mock", "offline"}:
        return "mock"
    if choice == "auto":
        if settings.GEMINI_API_KEY:
            return "gemini"
        if settings.OPENAI_API_KEY:
            return "openai"
        return "mock"
    if choice == "gemini" and not settings.GEMINI_API_KEY:
        return "mock"
    if choice == "openai" and not settings.OPENAI_API_KEY:
        return "mock"
    return choice


async def complete(prompt: str, *, system: Optional[str] = None) -> LLMResponse:
    backend = resolve_backend()
    try:
        if backend == "gemini":
            return await _gemini(prompt, system=system)
        if backend == "openai":
            return await _openai(prompt, system=system)
        if backend == "ollama":
            return await _ollama(prompt, system=system)
        return _mock(prompt)
    except Exception:
        logger.exception("LLM backend %s failed; using mock", backend)
        if backend != "mock":
            return _mock(prompt)
        raise


async def _gemini(prompt: str, *, system: Optional[str] = None) -> LLMResponse:
    primary = settings.DEFAULT_MODEL or "gemini-2.5-flash"
    fallback = settings.FALLBACK_MODEL or "gemini-flash-latest"
    models = [primary]
    if fallback and fallback != primary:
        models.append(fallback)
    # Hard safety net when Google retires the configured model id.
    for safety in ("gemini-2.5-flash", "gemini-flash-latest"):
        if safety not in models:
            models.append(safety)

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": settings.LLM_MAX_OUTPUT_TOKENS,
            "responseMimeType": "application/json",
        },
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    params = {"key": settings.GEMINI_API_KEY}
    last_error: Optional[Exception] = None
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        for model in models:
            url = f"{settings.GEMINI_BASE_URL.rstrip('/')}/models/{model}:generateContent"
            try:
                resp = await client.post(url, params=params, json=body)
                if resp.status_code >= 400:
                    # Retry without JSON mime for older/stricter model endpoints.
                    body_plain = {
                        **body,
                        "generationConfig": {
                            k: v
                            for k, v in body["generationConfig"].items()
                            if k != "responseMimeType"
                        },
                    }
                    resp = await client.post(url, params=params, json=body_plain)
                if resp.status_code == 404:
                    logger.warning("Gemini model unavailable: %s", model)
                    last_error = httpx.HTTPStatusError(
                        f"model {model} not found",
                        request=resp.request,
                        response=resp,
                    )
                    continue
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                last_error = exc
                logger.warning("Gemini model %s failed: %s", model, exc)
                continue

            text = ""
            try:
                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(
                    p.get("text", "") for p in parts if isinstance(p, dict)
                ).strip()
            except Exception:
                text = ""
            if not text:
                last_error = RuntimeError(f"Empty Gemini response: {data!r}")
                continue
            return LLMResponse(text=text, provider="gemini", model=model)

    if last_error:
        raise last_error
    raise RuntimeError("Gemini request failed for all configured models")


async def _openai(prompt: str, *, system: Optional[str] = None) -> LLMResponse:
    model = settings.OPENAI_MODEL or settings.DEFAULT_MODEL
    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": settings.LLM_MAX_OUTPUT_TOKENS,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        resp = await client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            body.pop("response_format", None)
            resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    text = (
        data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
    ).strip()
    if not text:
        raise RuntimeError(f"Empty OpenAI response: {data!r}")
    return LLMResponse(text=text, provider="openai", model=model)


async def _ollama(prompt: str, *, system: Optional[str] = None) -> LLMResponse:
    model = settings.OLLAMA_MODEL or settings.DEFAULT_MODEL
    url = f"{settings.OLLAMA_URL.rstrip('/')}/api/chat"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
    text = (
        (data.get("message") or {}).get("content", "") or data.get("response", "") or ""
    ).strip()
    if not text:
        raise RuntimeError(f"Empty Ollama response: {data!r}")
    return LLMResponse(text=text, provider="ollama", model=model)


def _mock(prompt: str) -> LLMResponse:
    match = re.search(r'"service"\s*:\s*"([^"]+)"', prompt)
    service = match.group(1) if match else settings.OTEL_SERVICE_NAME
    report = {
        "summary": (
            f"Aegis offline analysis for '{service}': error/latency signals were "
            "present in the investigation window. Configure a reasoner API key for live RCA."
        ),
        "affected_service": service,
        "root_cause": (
            "Application errors (HTTP 5xx / dependency failures) correlated with "
            "elevated latency. Offline reasoner — not a live model judgment."
        ),
        "impact": "Clients of failing endpoints may see 500/503 responses and higher latency.",
        "suggested_resolution": (
            "1) Inspect failing spans/logs in SigNoz. "
            "2) Reproduce with Fault injectors. "
            "3) Fix the failing path and re-check p95. "
            "4) Configure a reasoner key for full AI RCA."
        ),
        "confidence": "low",
    }
    return LLMResponse(
        text=json.dumps(report), provider="offline", model="aegis-offline"
    )
