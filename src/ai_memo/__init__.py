"""Top level package for the AI memo classifier.

The package exposes the :class:`~ai_memo.classifier.MemoClassifier` class
which can be used to classify free-form memo text into structured buckets.
"""

from .classifier import MemoClassifier, MemoAnalysis

__all__ = ["MemoClassifier", "MemoAnalysis"]
