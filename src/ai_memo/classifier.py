"""Heuristic classifier for unstructured memo text.

The goal of the classifier is to categorise loosely structured notes into one
of a small number of memo buckets.  The logic favours transparency and
predictability over machine learning by relying on keyword and pattern
matching.  This makes the behaviour easy to reason about and tweak when new
kinds of memos have to be handled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, Iterable, List, Sequence

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}(?!\d)"
)
DATE_PATTERN = re.compile(
    r"\b(?:(?:\d{1,2}[/-]){1,2}\d{2,4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2})\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(
    r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\b(?:[1-9]|1[0-2])(?:[:.][0-5]\d)?\s*(?:am|pm)\b",
    re.IGNORECASE,
)
DAY_PATTERN = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow|tonight)\b",
    re.IGNORECASE,
)


@dataclass
class MemoAnalysis:
    """Structured representation of the memo classification result."""

    category: str
    confidence: float
    details: Dict[str, object] = field(default_factory=dict)


class MemoClassifier:
    """Classify free-form memo text into memo categories.

    The classifier supports the following categories:

    ``phone``
        The memo references calling somebody or contains phone numbers.
    ``schedule``
        The memo is about scheduling or attending an event at a specific time.
    ``reminder``
        The memo asks the reader to remember or follow-up on a task.
    ``note``
        A general memo that does not fit the other categories.
    """

    PHONE_KEYWORDS: Sequence[str] = (
        "call",
        "dial",
        "phone",
        "telephone",
        "ring",
        "联系",
        "电话",
    )
    SCHEDULE_KEYWORDS: Sequence[str] = (
        "meet",
        "meeting",
        "appointment",
        "schedule",
        "安排",
        "会议",
        "约",
        "签到",
    )
    REMINDER_KEYWORDS: Sequence[str] = (
        "remember",
        "remind",
        "follow up",
        "todo",
        "task",
        "deadline",
        "提醒",
        "记得",
    )

    CATEGORY_PHONE = "phone"
    CATEGORY_SCHEDULE = "schedule"
    CATEGORY_REMINDER = "reminder"
    CATEGORY_NOTE = "note"
    DEFAULT_CATEGORY = CATEGORY_NOTE

    def __init__(self) -> None:
        self._keywords = {
            self.CATEGORY_PHONE: tuple(k.lower() for k in self.PHONE_KEYWORDS),
            self.CATEGORY_SCHEDULE: tuple(k.lower() for k in self.SCHEDULE_KEYWORDS),
            self.CATEGORY_REMINDER: tuple(k.lower() for k in self.REMINDER_KEYWORDS),
        }

    def classify(self, memo: str) -> MemoAnalysis:
        """Classify a memo string.

        Parameters
        ----------
        memo:
            Free-form memo text.

        Returns
        -------
        MemoAnalysis
            The predicted category and supporting details.
        """

        if not memo or not memo.strip():
            return MemoAnalysis(self.DEFAULT_CATEGORY, 0.0, {"reason": "empty"})

        text = memo.strip()
        lowered = text.lower()

        scores: Dict[str, float] = {
            self.CATEGORY_PHONE: 0.0,
            self.CATEGORY_SCHEDULE: 0.0,
            self.CATEGORY_REMINDER: 0.0,
        }
        details: Dict[str, object] = {}

        phone_numbers = self._extract_phone_numbers(text)
        if phone_numbers:
            scores[self.CATEGORY_PHONE] += 2.0
            details["phone_numbers"] = phone_numbers

        for category, keywords in self._keywords.items():
            matches = [kw for kw in keywords if kw in lowered]
            if matches:
                scores[category] += len(matches)
                details.setdefault("keyword_hits", {}).setdefault(category, matches)

        schedule_hits = self._extract_schedule_clues(text)
        if schedule_hits:
            scores[self.CATEGORY_SCHEDULE] += schedule_hits["score"]
            details.setdefault("schedule_clues", schedule_hits["matches"])

        reminder_hits = self._extract_reminder_clues(text)
        if reminder_hits:
            scores[self.CATEGORY_REMINDER] += reminder_hits["score"]
            details.setdefault("reminder_clues", reminder_hits["matches"])

        best_category, best_score = self._pick_category(scores)

        if best_score == 0:
            return MemoAnalysis(self.DEFAULT_CATEGORY, 0.2, details)

        # Confidence is a logistic-like squashing of the score to 0-1 range.
        confidence = min(0.95, 1 - 1 / (1 + best_score))
        return MemoAnalysis(best_category, confidence, details)

    def classify_batch(self, memos: Iterable[str]) -> List[MemoAnalysis]:
        """Classify multiple memos at once."""

        return [self.classify(memo) for memo in memos]

    def _extract_phone_numbers(self, text: str) -> List[str]:
        numbers = [match.group().strip() for match in PHONE_PATTERN.finditer(text)]
        return numbers

    def _extract_schedule_clues(self, text: str) -> Dict[str, object]:
        matches: Dict[str, List[str]] = {}
        score = 0.0

        dates = [match.group() for match in DATE_PATTERN.finditer(text)]
        if dates:
            matches["dates"] = dates
            score += 1.5

        times = [match.group() for match in TIME_PATTERN.finditer(text)]
        if times:
            matches["times"] = times
            score += 1.5

        days = [match.group() for match in DAY_PATTERN.finditer(text)]
        if days:
            matches["days"] = days
            score += 0.5

        return {"matches": matches, "score": score} if matches else {}

    def _extract_reminder_clues(self, text: str) -> Dict[str, object]:
        matches: Dict[str, List[str]] = {}
        score = 0.0

        bullet_points = [line.strip("-• ") for line in text.splitlines() if line.strip().startswith(("-", "•"))]
        if bullet_points:
            matches["bullets"] = bullet_points
            score += 1.0

        imperative_verbs = self._find_imperative_verbs(text)
        if imperative_verbs:
            matches["imperatives"] = imperative_verbs
            score += 0.5

        return {"matches": matches, "score": score} if matches else {}

    def _find_imperative_verbs(self, text: str) -> List[str]:
        imperatives: List[str] = []
        for token in re.split(r"[^A-Za-z\u4e00-\u9fff]+", text):
            if not token:
                continue
            lower = token.lower()
            if lower in {"submit", "send", "check", "pay", "call", "follow", "确认", "提交", "完成"}:
                imperatives.append(token)
        return imperatives

    def _pick_category(self, scores: Dict[str, float]) -> tuple[str, float]:
        best_category = self.DEFAULT_CATEGORY
        best_score = 0.0
        for category, score in scores.items():
            if score > best_score:
                best_category = category
                best_score = score
        return best_category, best_score


__all__ = ["MemoClassifier", "MemoAnalysis"]
