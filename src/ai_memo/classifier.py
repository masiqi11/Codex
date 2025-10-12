"""Memo parsing powered by the OpenAI API."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIRequestError(RuntimeError):
    """Raised when the OpenAI API cannot be reached or returns an error."""


@dataclass
class MemoClassification:
    """Structured representation returned by :class:`MemoParser`."""

    category: str
    confidence: float
    summary: str
    action_items: List[str] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)

    def to_ios_payload(self) -> Dict[str, Any]:
        """Return a dictionary ready for JSON encoding on iOS."""

        return {
            "category": self.category,
            "confidence": self.confidence,
            "summary": self.summary,
            "actionItems": self.action_items,
        }


class MemoParser:
    """Parse free-form memos by delegating understanding to an OpenAI model."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        endpoint: str = OPENAI_CHAT_COMPLETIONS_URL,
        requester: Optional[Callable[[str, Dict[str, Any], str], Dict[str, Any]]] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.endpoint = endpoint
        self._requester = requester or self._request

        if not self.api_key:
            raise ValueError(
                "An OpenAI API key is required. Pass it to MemoParser(api_key=...) "
                "or set the OPENAI_API_KEY environment variable."
            )

    def classify(self, memo: str, *, locale: str = "zh-CN") -> MemoClassification:
        """Send the memo to the OpenAI model and interpret the response."""

        memo = memo.strip()
        if not memo:
            raise ValueError("Memo text cannot be empty.")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an intelligent assistant that organises user memos into "
                        "structured reminders for an iOS application. Always reply with a "
                        "single JSON object that has the keys 'category', 'confidence', "
                        "'summary', and 'action_items'. The 'category' must be one of "
                        "['phone', 'schedule', 'reminder', 'note']. The 'confidence' "
                        "should be a number between 0 and 1. The 'summary' must be a "
                        "one-sentence recap suitable for display in an iOS notification. "
                        "'action_items' should be an array of concise follow-up actions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Locale: {locale}\n"
                        "Memo: {memo}\n"
                        "Respond in {locale} when appropriate."
                    ).format(locale=locale, memo=memo),
                },
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        data = self._requester(self.endpoint, payload, self.api_key)
        return self._parse_response(data)

    # ------------------------------------------------------------------
    # Networking helpers
    def _request(self, url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=encoded,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - network error handling
            detail = exc.read().decode("utf-8") if exc.fp else exc.reason
            raise OpenAIRequestError(f"OpenAI API returned {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network error handling
            raise OpenAIRequestError(f"Failed to contact OpenAI API: {exc.reason}") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:  # pragma: no cover - unexpected response
            raise OpenAIRequestError("OpenAI API response was not valid JSON") from exc

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_response(response: Dict[str, Any]) -> MemoClassification:
        try:
            message = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenAIRequestError("OpenAI API response did not include a message") from exc

        if isinstance(message, str):
            content = message
        else:
            raise OpenAIRequestError("Unexpected message content type from OpenAI")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OpenAIRequestError("OpenAI message was not valid JSON") from exc

        category = payload.get("category", "note")
        confidence = float(payload.get("confidence", 0))
        summary = payload.get("summary", "")
        action_items = payload.get("action_items", [])

        if not isinstance(action_items, list):
            action_items = [str(action_items)]
        action_items = [str(item) for item in action_items]

        return MemoClassification(
            category=str(category),
            confidence=confidence,
            summary=str(summary),
            action_items=action_items,
            raw_response=response,
        )
