import io

from ai_memo import MemoApp
from ai_memo.classifier import MemoClassification


class StubParser:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.calls: list[str] = []

    def classify(self, memo: str, *, locale: str = "zh-CN") -> MemoClassification:
        self.calls.append(memo)
        return MemoClassification(
            category="reminder",
            confidence=0.9,
            summary=f"请记得：{memo}",
            action_items=["检查日程"],
        )


def run_app_with_input(text: str, parser_factory=StubParser) -> tuple[int, str]:
    input_stream = io.StringIO(text)
    output_stream = io.StringIO()
    app = MemoApp(input_stream=input_stream, output_stream=output_stream, parser_factory=parser_factory)
    exit_code = app.run()
    return exit_code, output_stream.getvalue()


def test_app_configures_and_classifies():
    exit_code, output = run_app_with_input("sk-test\n\n给小王打电话\n\n")

    assert exit_code == 0
    assert "✅ 已配置完成" in output
    assert "给小王打电话" in output
    assert "后续行动" in output


def test_app_reconfigures_with_command():
    input_text = "sk-first\n\n:config\nsk-second\nother-model\n提醒我写周报\n\n"
    exit_code, output = run_app_with_input(input_text)

    assert exit_code == 0
    assert "当前模型：other-model" in output
    assert output.count("✅ 已配置完成") == 2


def test_app_exits_when_configuration_cancelled():
    exit_code, output = run_app_with_input("\n")

    assert exit_code == 1
    assert "未完成配置" in output
