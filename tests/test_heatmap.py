from __future__ import annotations

from papertrail.heatmap import generate_heatmap
from papertrail.store import Paper


def test_heatmap_empty() -> None:
    svg = generate_heatmap([], year=2025)
    assert "<svg" in svg
    assert "0 papers read in 2025" in svg


def test_heatmap_with_papers() -> None:
    papers = [
        Paper(title="Paper A", date_read="2025-03-15"),
        Paper(title="Paper B", date_read="2025-03-15"),
        Paper(title="Paper C", date_read="2025-06-01"),
    ]
    svg = generate_heatmap(papers, year=2025)
    assert "3 papers read in 2025" in svg
    assert "Paper A" in svg
    assert "2 papers" in svg  # tooltip for March 15


def test_heatmap_has_month_labels() -> None:
    svg = generate_heatmap([], year=2025)
    assert "Jan" in svg
    assert "Dec" in svg
