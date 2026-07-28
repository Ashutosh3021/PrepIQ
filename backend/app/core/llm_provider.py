"""
Env-driven LLM provider layer (Phase 1).

All text-generation / structured-JSON LLM calls should go through
`get_llm_client(capability)` so model names and API keys are never
hard-coded in routers, services, or engines.

Capabilities: "prediction" | "extraction" | "chat"
Resolution order (per capability):
  1. CAPABILITY_PROVIDER / CAPABILITY_MODEL / CAPABILITY_API_KEY / CAPABILITY_BASE_URL
  2. LLM_DEFAULT_*
  3. Legacy GEMINI_API_KEY (key only) + default provider/model
  4. Unavailable → client.is_available is False; callers keep existing fallbacks
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_CAPABILITIES = ("prediction", "extraction", "chat")
_lock = threading.Lock()
_clients: Dict[str, "LLMClient"] = {}


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def resolve_llm_settings(capability: str) -> Dict[str, str]:
    """Resolve provider/model/key/base_url for a capability."""
    cap = capability.strip().lower()
    if cap not in _CAPABILITIES:
        raise ValueError(f"Unknown LLM capability: {capability!r}; expected one of {_CAPABILITIES}")

    prefix = cap.upper()  # PREDICTION | EXTRACTION | CHAT

    provider = _env(f"{prefix}_PROVIDER") or _env("LLM_DEFAULT_PROVIDER") or "gemini"
    model = _env(f"{prefix}_MODEL") or _env("LLM_DEFAULT_MODEL") or "gemini-1.5-flash"
    api_key = (
        _env(f"{prefix}_API_KEY")
        or _env("LLM_DEFAULT_API_KEY")
        or _env("GEMINI_API_KEY")  # legacy compatibility
    )
    base_url = _env(f"{prefix}_BASE_URL") or _env("LLM_DEFAULT_BASE_URL")

    return {
        "capability": cap,
        "provider": provider.lower(),
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
    }


def _strip_code_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


class _TextResponse:
    """Minimal response object matching google.generativeai generate_content shape."""

    def __init__(self, text: str):
        self.text = text


class LLMClient:
    """Minimal unified LLM client surface used by PrepIQ call sites."""

    def __init__(self, settings: Dict[str, str]):
        self.capability = settings["capability"]
        self.provider = settings["provider"]
        self.model_name = settings["model"]
        self.api_key = settings["api_key"]
        self.base_url = settings.get("base_url") or ""
        self._backend: Any = None
        self._init_error: Optional[str] = None
        self._init_backend()

    def _init_backend(self) -> None:
        if not self.api_key:
            self._init_error = f"No API key for capability={self.capability}"
            logger.warning(
                "LLM unavailable for %s (%s): missing API key",
                self.capability,
                self.provider,
            )
            return

        if self.provider in ("gemini", "google", "google-generativeai"):
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._backend = genai.GenerativeModel(self.model_name)
                logger.info(
                    "LLM client ready capability=%s provider=gemini model=%s",
                    self.capability,
                    self.model_name,
                )
            except Exception as e:
                self._init_error = str(e)
                logger.error(
                    "Failed to init Gemini for %s model=%s: %s",
                    self.capability,
                    self.model_name,
                    e,
                )
            return

        self._init_error = f"Unsupported provider {self.provider!r} for capability={self.capability}"
        logger.warning(self._init_error)

    @property
    def is_available(self) -> bool:
        return self._backend is not None

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Return plain text from the configured model."""
        if not self.is_available:
            raise RuntimeError(
                self._init_error or f"LLM client unavailable for {self.capability}"
            )

        generation_config = kwargs.pop("generation_config", None)
        if self.provider in ("gemini", "google", "google-generativeai"):
            if generation_config is not None:
                response = self._backend.generate_content(
                    prompt, generation_config=generation_config
                )
            else:
                response = self._backend.generate_content(prompt)
            text = getattr(response, "text", None)
            if text is None:
                text = str(response)
            return (text or "").strip()

        raise RuntimeError(f"generate_text not implemented for provider={self.provider}")

    def generate_content(self, prompt: str, **kwargs: Any) -> _TextResponse:
        """
        Legacy-compatible method (same shape as google.generativeai GenerativeModel).
        Prefer generate_text / generate_json in new code.
        """
        text = self.generate_text(prompt, **kwargs)
        return _TextResponse(text)

    def generate_json(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate and parse a JSON object from the model.

        Optional kwargs:
          response_schema: dict — Gemini JSON schema (when supported)
          expect_list: bool — if True, accept a top-level JSON array and wrap as {"items": [...]}
        """
        expect_list = bool(kwargs.pop("expect_list", False))
        response_schema = kwargs.pop("response_schema", None)

        gen_kwargs: Dict[str, Any] = {}
        if self.provider in ("gemini", "google", "google-generativeai") and response_schema is not None:
            try:
                import google.generativeai as genai

                gen_kwargs["generation_config"] = genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                )
            except Exception as e:
                logger.warning("Could not apply Gemini JSON schema config: %s", e)

        raw = self.generate_text(prompt, **gen_kwargs)
        cleaned = _strip_code_fences(raw)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned non-JSON for {self.capability}: {e}") from e

        if expect_list:
            if isinstance(parsed, list):
                return {"items": parsed}
            if isinstance(parsed, dict):
                return parsed
            raise ValueError(f"Expected JSON list/object for {self.capability}")

        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object for {self.capability}, got {type(parsed)}")
        return parsed


def get_llm_client(capability: str) -> LLMClient:
    """
    Return a cached LLMClient for the capability.

    Safe to call when keys are missing: client.is_available will be False
    and generate_* will raise RuntimeError (callers keep try/except fallbacks).
    """
    cap = capability.strip().lower()
    settings = resolve_llm_settings(cap)
    cache_key = f"{settings['capability']}:{settings['provider']}:{settings['model']}:{bool(settings['api_key'])}"

    with _lock:
        client = _clients.get(cache_key)
        if client is None:
            client = LLMClient(settings)
            _clients[cache_key] = client
        return client


def clear_llm_client_cache() -> None:
    """Test helper: drop cached clients."""
    with _lock:
        _clients.clear()
