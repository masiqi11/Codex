"""Command line interface for the memo classifier."""
from __future__ import annotations

import argparse
import json
from typing import List

from .classifier import MemoClassifier


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify free-form memos")
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

    classifier = MemoClassifier()
    results = classifier.classify_batch(memos)

    if args.json:
        print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))
    else:
        for memo, result in zip(memos, results):
            print(f"Memo: {memo}")
            print(f"  Category   : {result.category}")
            print(f"  Confidence : {result.confidence:.2f}")
            if result.details:
                print("  Details    :")
                for key, value in result.details.items():
                    print(f"    {key}: {value}")
            print()

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
