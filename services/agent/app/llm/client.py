import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

import httpx


@dataclass(frozen=True)
class LLMConfig:
    """
    OpenAI-compatible LLM server config.

    Example for vLLM:
      base_url="http://localhost:8000"
      model="Qwen/Qwen2.5-Coder-14B-Instruct"
      api_key="EMPTY"
    """
    base_url: str
    model: str
    api_key: str = "EMPTY"
    timeout_s: float = 300.0  # 5 minutes default

    @staticmethod
    def from_env() -> "LLMConfig":
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:8000").rstrip("/")
        model = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
        api_key = os.getenv("LLM_API_KEY", "EMPTY")
        timeout_s = float(os.getenv("LLM_TIMEOUT_S", "300"))  # 5 minutes default
        return LLMConfig(base_url=base_url, model=model, api_key=api_key, timeout_s=timeout_s)


class LLMError(RuntimeError):
    pass


def _headers(api_key: str) -> Dict[str, str]:
    # Many local servers ignore the key, but some require a non-empty string.
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _normalize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure messages are in OpenAI chat format:
      [{"role":"system"|"user"|"assistant", "content":"..."}]
    """
    out: List[Dict[str, Any]] = []
    for m in messages:
        role = str(m.get("role", "")).strip()
        content = m.get("content", "")
        if not role:
            raise ValueError(f"Message missing role: {m}")
        if content is None:
            content = ""
        out.append({"role": role, "content": content})
    return out


def _extract_text_from_choice(choice: Dict[str, Any]) -> str:
    # OpenAI-like response: choices[0].message.content
    msg = choice.get("message") or {}
    content = msg.get("content")
    return content if isinstance(content, str) else ""


class LLMClient:
    """
    Minimal OpenAI-compatible chat client over HTTP.

    Supports:
      - chat() -> full text
      - stream_chat() -> yields text deltas

    Notes:
      - For streaming, expects SSE lines "data: {...}" ending with "data: [DONE]".
      - Works with vLLM OpenAI server and many compatible servers.
    """

    def __init__(self, cfg: Optional[LLMConfig] = None):
        self.cfg = cfg or LLMConfig.from_env()

    def chat(
        self,
        messages: List[Dict[str, Any]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 1400,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Non-streaming chat completion. Returns assistant text.
        """
        payload = {
            "model": self.cfg.model,
            "messages": _normalize_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        if stop:
            payload["stop"] = stop
        if extra:
            payload.update(extra)

        url = f"{self.cfg.base_url}/v1/chat/completions"
        try:
            with httpx.Client(timeout=self.cfg.timeout_s) as client:
                r = client.post(url, headers=_headers(self.cfg.api_key), json=payload)
        except httpx.RequestError as e:
            raise LLMError(f"LLM request failed to {url}: {e}") from e

        if r.status_code >= 400:
            # Try to include server error body
            body = r.text[:2000]
            raise LLMError(f"LLM error {r.status_code}: {body}")

        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            raise LLMError(f"LLM returned no choices: {json.dumps(data)[:2000]}")
        return _extract_text_from_choice(choices[0]).strip()

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 1400,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Iterator[str]:
        """
        Streaming chat completion. Yields text deltas.

        Expected SSE format:
          data: {"choices":[{"delta":{"content":"..."}}]}
          data: [DONE]
        """
        payload = {
            "model": self.cfg.model,
            "messages": _normalize_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True,
        }
        if stop:
            payload["stop"] = stop
        if extra:
            payload.update(extra)

        url = f"{self.cfg.base_url}/v1/chat/completions"

        try:
            # Use longer timeout for streaming - separate connect and read timeouts
            # For streaming, read timeout should be very long since chunks arrive over time
            # Use a large value (600s = 10 minutes) to allow for slow generation
            timeout = httpx.Timeout(
                connect=30.0,  # 30s to connect
                read=600.0,  # 10 minutes for reading stream (chunks arrive over time)
                write=30.0,  # 30s to write request
                pool=30.0  # 30s to get connection from pool
            )
            
            with httpx.Client(timeout=timeout) as client:
                with client.stream(
                    "POST",
                    url,
                    headers=_headers(self.cfg.api_key),
                    json=payload,
                ) as r:
                    if r.status_code >= 400:
                        body = r.read().decode("utf-8", errors="replace")[:2000]
                        raise LLMError(f"LLM stream error {r.status_code}: {body}")

                    for line in r.iter_lines():
                        if not line:
                            continue
                        # SSE usually sends: b"data: {...}"
                        if line.startswith("data:"):
                            chunk = line[len("data:") :].strip()
                        else:
                            # Some servers may send raw JSON lines
                            chunk = line.strip()

                        if chunk == "[DONE]":
                            break

                        # JSON parse
                        try:
                            obj = json.loads(chunk)
                        except json.JSONDecodeError:
                            # Not JSON? ignore
                            continue

                        # OpenAI streaming format: choices[0].delta.content
                        choices = obj.get("choices") or []
                        if not choices:
                            continue
                        delta = (choices[0].get("delta") or {})
                        text = delta.get("content")
                        if isinstance(text, str) and text:
                            yield text

        except httpx.TimeoutException as e:
            raise LLMError(
                f"LLM request timed out after {self.cfg.timeout_s}s. "
                f"The model might be slow or overloaded. Try increasing LLM_TIMEOUT_S in .env"
            ) from e
        except httpx.ConnectError as e:
            raise LLMError(
                f"Failed to connect to LLM server at {self.cfg.base_url}. "
                f"Make sure vLLM is running: curl {self.cfg.base_url}/v1/models"
            ) from e
        except httpx.RequestError as e:
            raise LLMError(f"LLM streaming request failed to {url}: {e}") from e
