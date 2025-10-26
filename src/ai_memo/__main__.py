"""Entry point for the interactive memo app."""
from __future__ import annotations

from .app import MemoApp


def main() -> int:
    """Launch the interactive memo application."""

    app = MemoApp()
    return app.run()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
