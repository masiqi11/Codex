"""Command line interface for the OpenAI powered memo parser."""
from __future__ import annotations

import argparse
import json
import os
from typing import List

from .classifier import MemoParser, OpenAIRequestError


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse memos using OpenAI models")
    parser.add_argument(
        "memo",
        nargs="*",
        help="Memo text. When omitted the tool reads from stdin.",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Read memos from a newline separated text file.",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (defaults to the OPENAI_API_KEY environment variable).",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output the classification results as JSON.",
    )
    return parser.parse_args(argv)


def _read_memos(args: argparse.Namespace) -> List[str]:
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            return [line.strip() for line in handle if line.strip()]

    if args.memo:
        return [" ".join(args.memo)]

    import sys

    data = sys.stdin.read().strip()
    return [line.strip() for line in data.splitlines() if line.strip()] if data else []


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    memos = _read_memos(args)

    try:
        parser = MemoParser(api_key=args.api_key, model=args.model)
    except ValueError as exc:
        raise SystemExit(str(exc))

    results = []
    for memo in memos:
        try:
            results.append(parser.classify(memo))
        except OpenAIRequestError as exc:
            raise SystemExit(f"OpenAI request failed: {exc}")

    if args.json:
        print(json.dumps([result.to_ios_payload() for result in results], ensure_ascii=False, indent=2))
    else:
        for memo, result in zip(memos, results):
            print(f"Memo: {memo}")
            print(f"  Category   : {result.category}")
            print(f"  Confidence : {result.confidence:.2f}")
            print(f"  Summary    : {result.summary}")
            if result.action_items:
                print("  Action Items:")
                for item in result.action_items:
                    print(f"    - {item}")
            print()

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
