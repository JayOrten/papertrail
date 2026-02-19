from __future__ import annotations

from datetime import date

import arxiv
import httpx

from papertrail.store import Paper


def fetch_arxiv(arxiv_id: str) -> Paper:
    clean_id = arxiv_id.replace("https://arxiv.org/abs/", "").replace(
        "http://arxiv.org/abs/", ""
    )
    client = arxiv.Client()
    search = arxiv.Search(id_list=[clean_id])
    results = list(client.results(search))
    if not results:
        raise SystemExit(f"No arXiv paper found for ID: {clean_id}")
    result = results[0]
    return Paper(
        title=result.title,
        authors=[a.name for a in result.authors],
        url=result.entry_id,
        date_read=date.today().isoformat(),
        source="arxiv",
        arxiv_id=clean_id,
    )


def fetch_doi(doi: str) -> Paper:
    url = f"https://api.crossref.org/works/{doi}"
    resp = httpx.get(url, timeout=15, follow_redirects=True)
    if resp.status_code != 200:
        raise SystemExit(f"CrossRef lookup failed for DOI: {doi} (HTTP {resp.status_code})")
    data = resp.json()["message"]
    title = data.get("title", ["Unknown"])[0]
    authors = []
    for a in data.get("author", []):
        name_parts = [a.get("given", ""), a.get("family", "")]
        authors.append(" ".join(p for p in name_parts if p))
    paper_url = data.get("URL")
    return Paper(
        title=title,
        authors=authors,
        url=paper_url,
        date_read=date.today().isoformat(),
        source="doi",
        doi=doi,
    )
