from __future__ import annotations

from papertrail.charts import (
    generate_authors,
    generate_cumulative,
    generate_monthly,
    generate_streak,
    generate_tags,
)
from papertrail.store import Paper


def _sample_papers() -> list[Paper]:
    return [
        Paper(
            title="Paper A",
            authors=["Alice", "Bob"],
            date_read="2025-01-10",
            tags=["ml", "nlp"],
        ),
        Paper(
            title="Paper B",
            authors=["Alice"],
            date_read="2025-02-15",
            tags=["ml"],
        ),
        Paper(
            title="Paper C",
            authors=["Charlie"],
            date_read="2025-02-16",
            tags=["cv"],
        ),
    ]


def test_streak_svg() -> None:
    svg = generate_streak(_sample_papers())
    assert "Current streak" in svg
    assert "Longest streak" in svg


def test_tags_svg() -> None:
    svg = generate_tags(_sample_papers())
    assert "ml" in svg
    assert "Top Tags" in svg


def test_tags_empty() -> None:
    svg = generate_tags([Paper(title="No tags")])
    assert "No tags yet" in svg


def test_monthly_svg() -> None:
    svg = generate_monthly(_sample_papers(), year=2025)
    assert "Papers per month" in svg


def test_cumulative_svg() -> None:
    svg = generate_cumulative(_sample_papers())
    assert "Cumulative" in svg


def test_cumulative_empty() -> None:
    svg = generate_cumulative([])
    assert "No papers yet" in svg


def test_authors_svg() -> None:
    svg = generate_authors(_sample_papers())
    assert "Alice" in svg
    assert "Top Authors" in svg


def test_authors_empty() -> None:
    svg = generate_authors([])
    assert "No authors yet" in svg
