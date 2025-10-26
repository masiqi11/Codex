import json
import pytest

from ai_memo import MemoParser, OpenAIRequestError


class StubRequester:
    def __init__(self, response: dict | None = None, *, raise_error: Exception | None = None):
        self.response = response or {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "category": "reminder",
                                "confidence": 0.9,
                                "summary": "提醒完成后续任务",
                                "action_items": ["完成剩余工作"],
                            }
                        )
                    }
                }
            ]
        }
        self.raise_error = raise_error
        self.calls: list[dict] = []

    def __call__(self, url: str, payload: dict, api_key: str) -> dict:
        self.calls.append({"url": url, "payload": payload, "api_key": api_key})
        if self.raise_error:
            raise self.raise_error
        return self.response


def test_memo_parser_sends_expected_payload():
    requester = StubRequester()
    parser = MemoParser(api_key="test", requester=requester)

    result = parser.classify("下午给客户回电", locale="zh-CN")

    assert result.category == "reminder"
    assert result.action_items == ["完成剩余工作"]
    assert result.to_ios_payload()["actionItems"] == ["完成剩余工作"]

    assert requester.calls, "The requester should have been invoked"
    call = requester.calls[0]
    assert call["url"].endswith("/chat/completions")
    assert call["api_key"] == "test"

    payload = call["payload"]
    assert payload["model"] == "gpt-4o-mini"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "system"
    assert "iOS" in payload["messages"][0]["content"]
    assert "下午给客户回电" in payload["messages"][1]["content"]


def test_memo_parser_requires_api_key():
    with pytest.raises(ValueError):
        MemoParser(api_key="")


def test_memo_parser_rejects_empty_memo():
    requester = StubRequester()
    parser = MemoParser(api_key="test", requester=requester)

    with pytest.raises(ValueError):
        parser.classify("   ")


def test_memo_parser_wraps_request_errors():
    requester = StubRequester(raise_error=OpenAIRequestError("boom"))
    parser = MemoParser(api_key="test", requester=requester)

    with pytest.raises(OpenAIRequestError):
        parser.classify("随时提醒我")


def test_invalid_response_raises_error():
    requester = StubRequester(response={"invalid": True})
    parser = MemoParser(api_key="test", requester=requester)

    with pytest.raises(OpenAIRequestError):
        parser.classify("无效响应")


def test_action_items_cast_to_list():
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "category": "note",
                            "confidence": 0.5,
                            "summary": "just a memo",
                            "action_items": "单独事项",
                        }
                    )
                }
            }
        ]
    }
    requester = StubRequester(response=payload)
    parser = MemoParser(api_key="test", requester=requester)

    result = parser.classify("记一下")
    assert result.action_items == ["单独事项"]
