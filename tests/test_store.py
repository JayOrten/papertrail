from __future__ import annotations

import json
from pathlib import Path

from papertrail.store import Paper, PaperStore


def test_add_and_load(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.json")
    paper = Paper(title="Test Paper", tags=["ml"], rating=4)
    store.add(paper)

    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].title == "Test Paper"
    assert loaded[0].tags == ["ml"]
    assert loaded[0].rating == 4
    assert loaded[0].id == paper.id


def test_remove(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.json")
    p1 = store.add(Paper(title="Paper 1"))
    p2 = store.add(Paper(title="Paper 2"))

    removed = store.remove(p1.id)
    assert removed is not None
    assert removed.title == "Paper 1"

    remaining = store.load()
    assert len(remaining) == 1
    assert remaining[0].id == p2.id


def test_remove_nonexistent(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.json")
    store.add(Paper(title="Paper 1"))
    assert store.remove("nonexistent") is None
    assert len(store.load()) == 1


def test_find(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.json")
    p = store.add(Paper(title="Findable"))
    assert store.find(p.id) is not None
    assert store.find("nope") is None


def test_json_roundtrip(tmp_path: Path) -> None:
    store = PaperStore(tmp_path / "papers.json")
    paper = Paper(
        title="Full Paper",
        authors=["Alice", "Bob"],
        url="https://example.com",
        tags=["ai", "ml"],
        rating=5,
        notes="Good paper",
        source="manual",
        arxiv_id="1234.5678",
        doi="10.1234/test",
    )
    store.add(paper)

    raw = json.loads((tmp_path / "papers.json").read_text())
    assert len(raw) == 1
    assert raw[0]["title"] == "Full Paper"
    assert raw[0]["authors"] == ["Alice", "Bob"]
