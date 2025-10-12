from ai_memo import MemoClassifier


def test_phone_classification():
    classifier = MemoClassifier()
    memo = "Call Alice at 555-1234 about the new contract."
    result = classifier.classify(memo)
    assert result.category == classifier.CATEGORY_PHONE
    assert "555-1234" in result.details.get("phone_numbers", [])
    assert result.confidence > 0.5


def test_schedule_classification():
    classifier = MemoClassifier()
    memo = "Meeting with Li Wei on 12/03 at 14:00 to discuss roadmap."
    result = classifier.classify(memo)
    assert result.category == classifier.CATEGORY_SCHEDULE
    assert "12/03" in result.details["schedule_clues"]["dates"]
    assert "14:00" in result.details["schedule_clues"]["times"]


def test_reminder_classification():
    classifier = MemoClassifier()
    memo = "- Submit expense report\n- Follow up with procurement"
    result = classifier.classify(memo)
    assert result.category == classifier.CATEGORY_REMINDER
    assert "bullets" in result.details.get("reminder_clues", {})


def test_default_note_category():
    classifier = MemoClassifier()
    memo = "Ideas for the Q3 offsite."
    result = classifier.classify(memo)
    assert result.category == classifier.CATEGORY_NOTE
    assert result.confidence <= 0.3
