"""Interactive console application for memo parsing."""
from __future__ import annotations

import sys
from typing import Callable, TextIO

from .classifier import DEFAULT_MODEL, MemoClassification, MemoParser, OpenAIRequestError


ParserFactory = Callable[..., MemoParser]


class MemoApp:
    """Simple interactive app that handles memo input and API configuration."""

    def __init__(
        self,
        *,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
        parser_factory: ParserFactory = MemoParser,
    ) -> None:
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout
        self.parser_factory = parser_factory
        self._parser: MemoParser | None = None

    # ------------------------------------------------------------------
    # Public API
    def run(self) -> int:
        """Run the memo application until the user exits."""

        self._write("📒 欢迎使用 AI 备忘录助手！")
        self._write("所有配置（API Key、模型选择）都可以在程序内随时调整。")
        self._write("输入 :config 可以重新配置，直接回车退出。")

        if not self._configure_parser():
            self._write("未完成配置，程序已退出。")
            return 1

        while True:
            memo = self._prompt("请输入备忘录 > ").strip()
            if not memo:
                self._write("👋 再见！")
                return 0

            if memo == ":config":
                if not self._configure_parser():
                    self._write("未完成配置，程序已退出。")
                    return 1
                continue

            try:
                assert self._parser is not None  # for type checkers
                result = self._parser.classify(memo, locale="zh-CN")
            except ValueError as exc:
                self._write(f"⚠️ 输入有误：{exc}")
                continue
            except OpenAIRequestError as exc:
                self._write(f"❌ OpenAI 请求失败：{exc}")
                continue

            self._display_result(memo, result)

    # ------------------------------------------------------------------
    # Internal helpers
    def _configure_parser(self) -> bool:
        """Prompt the user for API key and model configuration."""

        while True:
            api_key = self._prompt("请输入 OpenAI API Key（回车取消） > ").strip()
            if not api_key:
                return False

            model_prompt = f"请选择模型（默认 {DEFAULT_MODEL}） > "
            model = self._prompt(model_prompt).strip() or DEFAULT_MODEL

            try:
                self._parser = self.parser_factory(api_key=api_key, model=model)
                self._write(f"✅ 已配置完成，当前模型：{model}")
                return True
            except ValueError as exc:
                self._write(f"⚠️ 配置错误：{exc}")

    def _display_result(self, memo: str, result: MemoClassification) -> None:
        """Render the classification output to the console."""

        self._write("📌 解析完成：")
        self._write(f"  原文：{memo}")
        self._write(f"  类别：{result.category}")
        self._write(f"  置信度：{result.confidence:.2f}")
        self._write(f"  摘要：{result.summary}")
        if result.action_items:
            self._write("  后续行动：")
            for idx, item in enumerate(result.action_items, start=1):
                self._write(f"    {idx}. {item}")
        self._write("")

    def _prompt(self, message: str) -> str:
        self.output_stream.write(message)
        self.output_stream.flush()
        line = self.input_stream.readline()
        return line.rstrip("\n") if line else ""

    def _write(self, message: str) -> None:
        self.output_stream.write(message + "\n")
        self.output_stream.flush()
