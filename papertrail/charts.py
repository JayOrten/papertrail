from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from papertrail.store import Paper

FONT = 'font-family="system-ui, -apple-system, sans-serif"'
BG = "#303446"
TEXT = "#c6d0f5"
DIM = "#a5adce"
ACCENT = "#a6d189"
ACCENT2 = "#81c8be"
BAR_COLOR = "#8caaee"


def generate_streak(papers: list[Paper]) -> str:
    """Badge-style SVG showing current and longest streak."""
    today = date.today()
    dates_read = sorted({p.date_read for p in papers}, reverse=True)

    # Current streak
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

    # Longest streak
    all_dates = sorted({date.fromisoformat(d) for d in dates_read})
    longest = 0
    run = 1
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
    """Tag cloud SVG sized by frequency."""
    tag_counts: Counter[str] = Counter()
    for p in papers:
        for t in p.tags:
            tag_counts[t] += 1

    if not tag_counts:
        return _empty_svg("No tags yet", 400, 80)

    top = tag_counts.most_common(top_n)
    max_count = top[0][1]

    # Layout tags in rows
    tags_svg = []
    x, y = 20, 35
    for tag, count in top:
        size = 11 + int((count / max_count) * 10)
        text_width = len(tag) * (size * 0.6) + 16

        if x + text_width > 380:
            x = 20
            y += 30

        # Pill background
        tags_svg.append(
            f'  <rect x="{x}" y="{y - size + 2}" width="{text_width:.0f}" '
            f'height="{size + 10}" rx="{(size + 10) // 2}" fill="#414559"/>'
        )
        tags_svg.append(
            f'  <text x="{x + 8}" y="{y + 6}" fill="{TEXT}" font-size="{size}" {FONT}>'
            f"{tag} ({count})</text>"
        )
        x += text_width + 8

    height = y + 40
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="20" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Top Tags</text>
{"".join(chr(10) + s for s in tags_svg)}
</svg>"""


def generate_monthly(papers: list[Paper], year: int | None = None) -> str:
    """Monthly bar chart for the given year."""
    if year is None:
        year = date.today().year

    monthly: list[int] = [0] * 12
    for p in papers:
        if p.date_read.startswith(str(year)):
            month = int(p.date_read[5:7])
            monthly[month - 1] += 1

    max_val = max(monthly) if any(monthly) else 1
    bar_width = 28
    chart_height = 120
    margin_left = 40
    margin_top = 30
    width = margin_left + 12 * (bar_width + 6) + 20
    height = margin_top + chart_height + 40

    bars = []
    months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    for i, count in enumerate(monthly):
        bh = int((count / max_val) * chart_height) if max_val else 0
        x = margin_left + i * (bar_width + 6)
        y = margin_top + chart_height - bh
        bars.append(
            f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{bh}" '
            f'rx="3" fill="{BAR_COLOR}"><title>{months[i]}: {count} papers</title></rect>'
        )
        # Month label
        bars.append(
            f'  <text x="{x + bar_width // 2}" y="{margin_top + chart_height + 16}" '
            f'text-anchor="middle" fill="{DIM}" font-size="10" {FONT}>{months[i]}</text>'
        )
        # Count above bar
        if count > 0:
            bars.append(
                f'  <text x="{x + bar_width // 2}" y="{y - 4}" text-anchor="middle" '
                f'fill="{DIM}" font-size="10" {FONT}>{count}</text>'
            )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="{margin_left}" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>
    Papers per month ({year})</text>
{"".join(chr(10) + s for s in bars)}
</svg>"""


def generate_cumulative(papers: list[Paper]) -> str:
    """Cumulative line graph of total papers over time."""
    if not papers:
        return _empty_svg("No papers yet", 400, 180)

    sorted_papers = sorted(papers, key=lambda p: p.date_read)
    first_date = date.fromisoformat(sorted_papers[0].date_read)
    last_date = date.today()
    total_days = (last_date - first_date).days or 1

    width = 400
    height = 180
    chart_left = 45
    chart_right = width - 15
    chart_top = 30
    chart_bottom = height - 30
    chart_width = chart_right - chart_left
    chart_height = chart_bottom - chart_top

    # Build cumulative data
    day_counts: Counter[str] = Counter()
    for p in sorted_papers:
        day_counts[p.date_read] += 1

    points = []
    cumulative = 0
    current = first_date
    while current <= last_date:
        cumulative += day_counts.get(current.isoformat(), 0)
        day_offset = (current - first_date).days
        x = chart_left + (day_offset / total_days) * chart_width
        y = chart_bottom - (cumulative / len(papers)) * chart_height
        points.append(f"{x:.1f},{y:.1f}")
        current += timedelta(days=1)

    polyline = " ".join(points)

    # Fill area
    fill_points = f"{chart_left},{chart_bottom} {polyline} {chart_right},{chart_bottom}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="{chart_left}" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>
    Cumulative papers read</text>
  <polygon points="{fill_points}" fill="{BAR_COLOR}" opacity="0.3"/>
  <polyline points="{polyline}" fill="none" stroke="{ACCENT}" stroke-width="2"/>
  <text x="{chart_left}" y="{chart_bottom + 18}" fill="{DIM}" font-size="10" {FONT}>
    {first_date.strftime("%b %Y")}</text>
  <text x="{chart_right}" y="{chart_bottom + 18}" text-anchor="end" fill="{DIM}" font-size="10" {FONT}>
    {last_date.strftime("%b %Y")}</text>
  <text x="{chart_left - 5}" y="{chart_bottom}" text-anchor="end" fill="{DIM}" font-size="10" {FONT}>0</text>
  <text x="{chart_left - 5}" y="{chart_top + 5}" text-anchor="end" fill="{DIM}" font-size="10" {FONT}>
    {len(papers)}</text>
</svg>"""


def generate_authors(papers: list[Paper], top_n: int = 8) -> str:
    """Horizontal bar chart of most-read authors."""
    author_counts: Counter[str] = Counter()
    for p in papers:
        for a in p.authors:
            author_counts[a] += 1

    if not author_counts:
        return _empty_svg("No authors yet", 400, 80)

    top = author_counts.most_common(top_n)
    max_count = top[0][1]

    bar_height = 20
    gap = 6
    margin_top = 30
    margin_left = 150
    chart_width = 220
    height = margin_top + len(top) * (bar_height + gap) + 10
    width = 400

    bars = []
    for i, (author, count) in enumerate(top):
        y = margin_top + i * (bar_height + gap)
        bw = int((count / max_count) * chart_width)

        # Truncate long author names
        display_name = author if len(author) <= 20 else author[:18] + ".."

        bars.append(
            f'  <text x="{margin_left - 8}" y="{y + bar_height - 5}" text-anchor="end" '
            f'fill="{TEXT}" font-size="11" {FONT}>{display_name}</text>'
        )
        bars.append(
            f'  <rect x="{margin_left}" y="{y}" width="{bw}" height="{bar_height}" '
            f'rx="3" fill="{BAR_COLOR}"><title>{author}: {count}</title></rect>'
        )
        bars.append(
            f'  <text x="{margin_left + bw + 6}" y="{y + bar_height - 5}" '
            f'fill="{DIM}" font-size="11" {FONT}>{count}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="20" y="18" fill="{TEXT}" font-size="13" font-weight="600" {FONT}>Top Authors</text>
{"".join(chr(10) + s for s in bars)}
</svg>"""


def _empty_svg(message: str, width: int, height: int) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" rx="6"/>
  <text x="{width // 2}" y="{height // 2 + 5}" text-anchor="middle"
    fill="{DIM}" font-size="13" {FONT}>{message}</text>
</svg>"""
