#!/usr/bin/env python3
"""Generate all SVGs and the profile README from papers.json.

Self-contained — only requires jinja2. No papertrail package needed.
Run from the profile repo root:
    python profile/generate.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

try:
    from jinja2 import Template
except ImportError:
    sys.exit("jinja2 not installed. Run: pip install jinja2")

# --- Style ---
FONT = 'font-family="system-ui, -apple-system, sans-serif"'
BG = "#303446"
TEXT = "#c6d0f5"
DIM = "#a5adce"
ACCENT = "#a6d189"
ACCENT2 = "#81c8be"
BAR_COLOR = "#8caaee"
HEATMAP_COLORS = ["#414559", "#4e6350", "#5a8147", "#80a86b", "#a6d189"]
CELL_SIZE = 13
CELL_GAP = 3
CELL_STEP = CELL_SIZE + CELL_GAP
H_MARGIN_LEFT = 40
H_MARGIN_TOP = 50
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", "Sun"]


# --- Data ---
class Paper:
    def __init__(self, **kwargs: object) -> None:
        self.id: str = kwargs.get("id", "")
        self.title: str = kwargs.get("title", "")
        self.authors: list[str] = kwargs.get("authors", [])
        self.url: str | None = kwargs.get("url")
        self.date_read: str = kwargs.get("date_read", date.today().isoformat())
        self.tags: list[str] = kwargs.get("tags", [])
        self.notes: str | None = kwargs.get("notes")
        self.rating: int | None = kwargs.get("rating")
        self.source: str | None = kwargs.get("source")
        self.arxiv_id: str | None = kwargs.get("arxiv_id")
        self.doi: str | None = kwargs.get("doi")


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _empty_svg(message: str, width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<rect width="100%" height="100%" fill="{BG}" rx="6"/>'
        f'<text x="{width // 2}" y="{height // 2 + 5}" text-anchor="middle" fill="{DIM}" font-size="13" {FONT}>{message}</text>'
        f'</svg>'
    )


# --- SVG Generators ---

def generate_heatmap(papers: list[Paper], year: int | None = None) -> str:
    if year is None:
        year = date.today().year
    year_papers = [p for p in papers if p.date_read.startswith(str(year))]
    day_counts: Counter[str] = Counter()
    day_titles: dict[str, list[str]] = {}
    for p in year_papers:
        day_counts[p.date_read] += 1
        day_titles.setdefault(p.date_read, []).append(p.title)
    max_count = max(day_counts.values()) if day_counts else 0

    jan1 = date(year, 1, 1)
    start = jan1 - timedelta(days=jan1.weekday())
    rects, month_x = [], {}

    for week in range(53):
        for dow in range(7):
            d = start + timedelta(weeks=week, days=dow)
            if d.year != year and d < jan1:
                continue
            if d.year != year and d > date(year, 12, 31):
                continue
            x = H_MARGIN_LEFT + week * CELL_STEP
            y = H_MARGIN_TOP + dow * CELL_STEP
            iso = d.isoformat()
            count = day_counts.get(iso, 0)
            if count == 0 or max_count == 0:
                color = HEATMAP_COLORS[0]
            else:
                idx = min(int((count / max_count) * (len(HEATMAP_COLORS) - 1)) + 1, len(HEATMAP_COLORS) - 1)
                color = HEATMAP_COLORS[idx]
            titles = day_titles.get(iso, [])
            tip = [iso]
            if count:
                tip.append(f"{count} paper{'s' if count != 1 else ''}")
                tip.extend(f"  - {_esc(t)}" for t in titles[:5])
            tooltip = "&#10;".join(tip)
            rects.append(
                f'  <rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="2" ry="2" fill="{color}"><title>{tooltip}</title></rect>'
            )
            if d.day <= 7 and d.month not in month_x:
                month_x[d.month] = x

    width = H_MARGIN_LEFT + 53 * CELL_STEP + 10
    height = H_MARGIN_TOP + 7 * CELL_STEP + 10
    ml = [f'  <text x="{x}" y="{H_MARGIN_TOP - 8}" fill="{DIM}" font-size="11" {FONT}>{MONTH_NAMES[m - 1]}</text>' for m, x in sorted(month_x.items())]
    dl = [f'  <text x="{H_MARGIN_LEFT - 8}" y="{H_MARGIN_TOP + i * CELL_STEP + CELL_SIZE - 2}" text-anchor="end" fill="{DIM}" font-size="10" {FONT}>{lab}</text>' for i, lab in enumerate(DAY_LABELS) if lab]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="{H_MARGIN_LEFT}" y="18" fill="{TEXT}" font-size="14" font-weight="600" {FONT}>{len(year_papers)} papers read in {year}</text>
{chr(10).join(ml)}
{chr(10).join(dl)}
{chr(10).join(rects)}
</svg>"""


def generate_streak(papers: list[Paper]) -> str:
    today = date.today()
    dates_read = sorted({p.date_read for p in papers}, reverse=True)
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
    all_dates = sorted({date.fromisoformat(d) for d in dates_read})
    longest, run = 0, 1
    for i in range(1, len(all_dates)):
        if (all_dates[i] - all_dates[i - 1]).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
    longest = max(longest, run) if all_dates else 0
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="320" height="60">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="20" y="25" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Current streak</text>
  <text x="20" y="45" fill="{ACCENT}" font-size="20" font-weight="700" {FONT}>{current} days</text>
  <text x="180" y="25" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Longest streak</text>
  <text x="180" y="45" fill="{ACCENT2}" font-size="20" font-weight="700" {FONT}>{longest} days</text>
</svg>"""


def generate_tags(papers: list[Paper], top_n: int = 12) -> str:
    tag_counts: Counter[str] = Counter()
    for p in papers:
        for t in p.tags:
            tag_counts[t] += 1
    if not tag_counts:
        return _empty_svg("No tags yet", 400, 80)
    top = tag_counts.most_common(top_n)
    max_count = top[0][1]
    parts = []
    x, y = 20, 35
    for tag, count in top:
        size = 11 + int((count / max_count) * 10)
        tw = len(tag) * (size * 0.6) + 16
        if x + tw > 380:
            x = 20
            y += 30
        parts.append(f'  <rect x="{x}" y="{y - size + 2}" width="{tw:.0f}" height="{size + 10}" rx="{(size + 10) // 2}" fill="#414559"/>')
        parts.append(f'  <text x="{x + 8}" y="{y + 6}" fill="{TEXT}" font-size="{size}" {FONT}>{_esc(tag)} ({count})</text>')
        x += tw + 8
    h = y + 40
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{h}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="20" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Top Tags</text>
{chr(10).join(parts)}
</svg>"""


def generate_monthly(papers: list[Paper], year: int | None = None) -> str:
    if year is None:
        year = date.today().year
    monthly = [0] * 12
    for p in papers:
        if p.date_read.startswith(str(year)):
            monthly[int(p.date_read[5:7]) - 1] += 1
    max_val = max(monthly) if any(monthly) else 1
    bw, ch, ml, mt = 28, 120, 40, 30
    width = ml + 12 * (bw + 6) + 20
    height = mt + ch + 40
    months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    bars = []
    for i, count in enumerate(monthly):
        bh = int((count / max_val) * ch) if max_val else 0
        x = ml + i * (bw + 6)
        y = mt + ch - bh
        bars.append(f'  <rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="3" fill="{BAR_COLOR}"><title>{months[i]}: {count}</title></rect>')
        bars.append(f'  <text x="{x + bw // 2}" y="{mt + ch + 16}" text-anchor="middle" fill="{DIM}" font-size="10" {FONT}>{months[i]}</text>')
        if count > 0:
            bars.append(f'  <text x="{x + bw // 2}" y="{y - 4}" text-anchor="middle" fill="{DIM}" font-size="10" {FONT}>{count}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="{ml}" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Papers per month ({year})</text>
{chr(10).join(bars)}
</svg>"""


def generate_cumulative(papers: list[Paper]) -> str:
    if not papers:
        return _empty_svg("No papers yet", 400, 180)
    sorted_papers = sorted(papers, key=lambda p: p.date_read)
    first = date.fromisoformat(sorted_papers[0].date_read)
    last = date.today()
    total_days = (last - first).days or 1
    w, h = 400, 180
    cl, cr, ct, cb = 45, w - 15, 30, h - 30
    cw, ch2 = cr - cl, cb - ct
    dc: Counter[str] = Counter()
    for p in sorted_papers:
        dc[p.date_read] += 1
    points = []
    cum = 0
    cur = first
    while cur <= last:
        cum += dc.get(cur.isoformat(), 0)
        dx = (cur - first).days
        x = cl + (dx / total_days) * cw
        y = cb - (cum / len(papers)) * ch2
        points.append(f"{x:.1f},{y:.1f}")
        cur += timedelta(days=1)
    poly = " ".join(points)
    fill = f"{cl},{cb} {poly} {cr},{cb}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="{cl}" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Cumulative papers read</text>
  <polygon points="{fill}" fill="{BAR_COLOR}" opacity="0.3"/>
  <polyline points="{poly}" fill="none" stroke="{ACCENT}" stroke-width="2"/>
  <text x="{cl}" y="{cb + 18}" fill="{DIM}" font-size="10" {FONT}>{first.strftime("%b %Y")}</text>
  <text x="{cr}" y="{cb + 18}" text-anchor="end" fill="{DIM}" font-size="10" {FONT}>{last.strftime("%b %Y")}</text>
  <text x="{cl - 5}" y="{cb}" text-anchor="end" fill="{DIM}" font-size="10" {FONT}>0</text>
  <text x="{cl - 5}" y="{ct + 5}" text-anchor="end" fill="{DIM}" font-size="10" {FONT}>{len(papers)}</text>
</svg>"""


def generate_authors(papers: list[Paper], top_n: int = 8) -> str:
    ac: Counter[str] = Counter()
    for p in papers:
        for a in p.authors:
            ac[a] += 1
    if not ac:
        return _empty_svg("No authors yet", 400, 80)
    top = ac.most_common(top_n)
    mc = top[0][1]
    bh, gap, mt, ml, cw = 20, 6, 30, 150, 220
    h = mt + len(top) * (bh + gap) + 10
    bars = []
    for i, (author, count) in enumerate(top):
        y = mt + i * (bh + gap)
        bw = int((count / mc) * cw)
        name = author if len(author) <= 20 else author[:18] + ".."
        bars.append(f'  <text x="{ml - 8}" y="{y + bh - 5}" text-anchor="end" fill="{TEXT}" font-size="11" {FONT}>{_esc(name)}</text>')
        bars.append(f'  <rect x="{ml}" y="{y}" width="{bw}" height="{bh}" rx="3" fill="{BAR_COLOR}"><title>{_esc(author)}: {count}</title></rect>')
        bars.append(f'  <text x="{ml + bw + 6}" y="{y + bh - 5}" fill="{DIM}" font-size="11" {FONT}>{count}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{h}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="20" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Top Authors</text>
{chr(10).join(bars)}
</svg>"""


# --- Main ---
def main() -> None:
    repo_root = Path(__file__).parent.parent
    papers_path = repo_root / "data" / "papers.json"

    if not papers_path.exists():
        print("No data/papers.json found. Nothing to generate.")
        return

    papers = [Paper(**p) for p in json.loads(papers_path.read_text())]
    print(f"Loaded {len(papers)} papers.")

    images_dir = repo_root / "images"
    images_dir.mkdir(exist_ok=True)

    for name, content in {
        "heatmap.svg": generate_heatmap(papers),
        "streak.svg": generate_streak(papers),
        "tags.svg": generate_tags(papers),
        "monthly.svg": generate_monthly(papers),
        "cumulative.svg": generate_cumulative(papers),
        "authors.svg": generate_authors(papers),
    }.items():
        (images_dir / name).write_text(content)
        print(f"  Generated images/{name}")

    template_path = repo_root / "profile" / "README.md.template"
    if template_path.exists():
        template = Template(template_path.read_text())
        recent = sorted(papers, key=lambda p: p.date_read, reverse=True)[:10]
        readme = template.render(
            username=repo_root.name,
            papers=papers,
            recent_papers=recent,
        )
        (repo_root / "README.md").write_text(readme)
        print("  Generated README.md")

    print("Done.")


if __name__ == "__main__":
    main()
