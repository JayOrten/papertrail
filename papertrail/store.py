from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field


class Paper(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str
    authors: list[str] = Field(default_factory=list)
    url: str | None = None
    date_read: str = Field(default_factory=lambda: date.today().isoformat())
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    rating: int | None = None
    source: str | None = None
    arxiv_id: str | None = None
    doi: str | None = None


class PaperStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _ensure_file(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]")

    def load(self) -> list[Paper]:
        self._ensure_file()
        data = json.loads(self.path.read_text())
        return [Paper(**p) for p in data]

    def save(self, papers: list[Paper]) -> None:
        self._ensure_file()
        self.path.write_text(
            json.dumps([p.model_dump() for p in papers], indent=2) + "\n"
        )

    def add(self, paper: Paper) -> Paper:
        papers = self.load()
        papers.append(paper)
        self.save(papers)
        return paper

    def remove(self, paper_id: str) -> Paper | None:
        papers = self.load()
        for i, p in enumerate(papers):
            if p.id == paper_id:
                removed = papers.pop(i)
                self.save(papers)
                return removed
        return None

    def find(self, paper_id: str) -> Paper | None:
        for p in self.load():
            if p.id == paper_id:
                return p
        return None
