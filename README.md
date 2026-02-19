# papertrail

Track academic papers you read. Visualize them as a GitHub-style contribution heatmap on your profile.

## Install

```bash
pip install .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
# Set up config and profile repo
papertrail init

# Add papers
papertrail add "Attention Is All You Need" --tags transformers,nlp --rating 5
papertrail add --arxiv 1706.03762
papertrail add --doi 10.1038/s41586-021-03819-2

# Browse
papertrail list
papertrail search "attention"
papertrail stats

# Push to GitHub (triggers profile update)
papertrail sync
```

## Commands

| Command | Description |
|---|---|
| `papertrail init` | Configure GitHub username and profile repo path |
| `papertrail add "Title"` | Add a paper manually |
| `papertrail add --arxiv ID` | Add from ArXiv (auto-fetches metadata) |
| `papertrail add --doi DOI` | Add from DOI (auto-fetches metadata) |
| `papertrail list` | List papers (filter by `--year`, `--month`, `--tag`, `--rating-min`) |
| `papertrail search "query"` | Search titles, authors, notes, tags |
| `papertrail stats` | Reading statistics |
| `papertrail remove ID` | Remove a paper |
| `papertrail sync` | Commit and push papers.json |

## Profile Visualizations

The tool generates these SVGs for your GitHub profile:

- **Heatmap** — GitHub-style contribution grid
- **Streak counter** — Current and longest reading streaks
- **Monthly bar chart** — Papers per month
- **Cumulative graph** — Total papers over time
- **Tag cloud** — Most-used tags
- **Top authors** — Most-read authors
- **Recent papers table** — Last 10 papers in the README

## Adopting for Your Own Profile

1. Install: `pip install papertrail` (or clone and `pip install .`)
2. Run `papertrail init` — enter your GitHub username and where to clone your profile repo
3. Create a GitHub profile repo (`username/username`) if you don't have one
4. Start adding papers and run `papertrail sync`
5. The GitHub Action regenerates your profile on each sync
