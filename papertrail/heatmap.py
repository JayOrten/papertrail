from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from papertrail.store import Paper

# Catppuccin Frappe color scale
COLORS = ["#414559", "#4e6350", "#5a8147", "#80a86b", "#a6d189"]
CELL_SIZE = 13
CELL_GAP = 3
CELL_STEP = CELL_SIZE + CELL_GAP
MARGIN_LEFT = 40
MARGIN_TOP = 30

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
DAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", "Sun"]


def _color_for_count(count: int, max_count: int) -> str:
    if count == 0:
        return COLORS[0]
    if max_count == 0:
        return COLORS[0]
    ratio = count / max_count
    idx = min(int(ratio * (len(COLORS) - 1)) + 1, len(COLORS) - 1)
    return COLORS[idx]


def generate_heatmap(papers: list[Paper], year: int | None = None) -> str:
    if year is None:
        year = date.today().year

    # Count papers per day and collect titles
    day_counts: Counter[str] = Counter()
    day_titles: dict[str, list[str]] = {}
    for p in papers:
        if p.date_read.startswith(str(year)):
            day_counts[p.date_read] += 1
            day_titles.setdefault(p.date_read, []).append(p.title)

    max_count = max(day_counts.values()) if day_counts else 0

    # Build grid: 53 weeks x 7 days
    jan1 = date(year, 1, 1)
    start = jan1 - timedelta(days=jan1.weekday())  # Monday of week containing Jan 1

    rects = []
    month_x: dict[int, int] = {}

    for week in range(53):
        for dow in range(7):
            d = start + timedelta(weeks=week, days=dow)
            if d.year != year and d < jan1:
                continue
            if d.year != year and d > date(year, 12, 31):
                continue

            x = MARGIN_LEFT + week * CELL_STEP
            y = MARGIN_TOP + dow * CELL_STEP

            iso = d.isoformat()
            count = day_counts.get(iso, 0)
            color = _color_for_count(count, max_count)

            titles = day_titles.get(iso, [])
            tooltip_parts = [iso]
            if count:
                tooltip_parts.append(f"{count} paper{'s' if count != 1 else ''}")
                for t in titles[:5]:
                    tooltip_parts.append(f"  - {t}")

            tooltip = "&#10;".join(tooltip_parts)

            rects.append(
                f'  <rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="2" ry="2" fill="{color}">'
                f"<title>{tooltip}</title></rect>"
            )

            # Track first x position for each month
            if d.day <= 7 and d.month not in month_x:
                month_x[d.month] = x

    width = MARGIN_LEFT + 53 * CELL_STEP + 10
    height = MARGIN_TOP + 7 * CELL_STEP + 10

    # Month labels
    month_labels_svg = []
    for m, x in sorted(month_x.items()):
        month_labels_svg.append(
            f'  <text x="{x}" y="{MARGIN_TOP - 8}" '
            f'fill="#a5adce" font-size="11" font-family="system-ui, -apple-system, sans-serif">'
            f"{MONTH_LABELS[m - 1]}</text>"
        )

    # Day labels
    day_labels_svg = []
    for i, label in enumerate(DAY_LABELS):
        if label:
            y = MARGIN_TOP + i * CELL_STEP + CELL_SIZE - 2
            day_labels_svg.append(
                f'  <text x="{MARGIN_LEFT - 8}" y="{y}" text-anchor="end" '
                f'fill="#a5adce" font-size="10" font-family="system-ui, -apple-system, sans-serif">'
                f"{label}</text>"
            )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="#303446" rx="6"/>
  <text x="{MARGIN_LEFT}" y="18" fill="#c6d0f5" font-size="14" font-weight="600"
    font-family="system-ui, -apple-system, sans-serif">
    {len(papers)} papers read in {year}</text>
{"".join(chr(10) + s for s in month_labels_svg)}
{"".join(chr(10) + s for s in day_labels_svg)}
{"".join(chr(10) + s for s in rects)}
</svg>"""

    return svg
