from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from papertrail.store import Paper, PaperStore


def test_stats_streak_calculation(tmp_path: Path) -> None:
    """Verify streak logic by creating papers on consecutive days."""
    store = PaperStore(tmp_path / "papers.json")
    today = date.today()
    for i in range(5):
        d = today - timedelta(days=i)
        store.add(Paper(title=f"Day {i}", date_read=d.isoformat()))

    papers = store.load()
    dates_read = sorted({p.date_read for p in papers}, reverse=True)

    # Current streak should be 5
    current = 0
    check = today
    for _ in range(len(dates_read) + 1):
        if check.isoformat() in dates_read:
            current += 1
            check -= timedelta(days=1)
        elif check == today:
            check -= timedelta(days=1)
        else:
            break

    assert current == 5


def test_tag_counting(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.json")
    store.add(Paper(title="P1", tags=["ml", "nlp"]))
    store.add(Paper(title="P2", tags=["ml"]))
    store.add(Paper(title="P3", tags=["cv", "ml"]))

    papers = store.load()
    tag_counts: dict[str, int] = {}
    for p in papers:
        for t in p.tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    assert tag_counts["ml"] == 3
    assert tag_counts["nlp"] == 1
    assert tag_counts["cv"] == 1
